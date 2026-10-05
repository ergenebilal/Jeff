/* One continuous, interruptible call. No recognition restart or per-turn send button. */
(function(root){
  class JeffLiveCall {
    constructor({state,transcript,notice,voice,worklet}){
      Object.assign(this,{state,transcript,notice,voice,worklet});
      this.active=false; this.generation=0; this.sources=new Set(); this.pending=new Map();
      this.stats={inputFrames:0,outputChunks:0,interruptions:0,localInterruptions:0,unconsultedAudioDropped:0};
      this.timings=[];this.speechEndedAt=null;this.voiceTurn=null;
      this.dialogue=[];
      this.inputText='';this.outputText='';
      this.heldAudio=[];this.heldBytes=0;this.heldText='';this.completedCalls=new Set();
      this.background=new Map();this.resultAnnouncements=[];this.socketEpoch=0;
    }
    async start(){
      if(this.active)return;
      if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia)
        throw new Error('Mikrofon için güvenli panel adresini açın.');
      this.active=true; const generation=++this.generation;
      this.connectionTiming={startedAt:performance.now(),tokenAt:null,socketAt:null,microphoneAt:null,readyAt:null};
      const current=()=>this.active && this.generation===generation;
      this.state('connecting','Görüşme bağlanıyor');
      this.ctx=new (window.AudioContext||window.webkitAudioContext)();
      await this.ctx.resume(); // Executed from the owner's click, including on mobile.
      try{
        await this.contextQueue?.tail; // Finish this tab's previous context before reopening.
        this.session=await this.post('session',{voice:this.voice()});
        this.connectionTiming.tokenAt=performance.now();
        if(!current()){this.post('end',{session:this.session.session}).catch(()=>{});this.session=null;return;}
        const session=this.session;this.fastDialogue=new Set(session.fast_dialogue_phrases||[]);
        this.dialogue=(session.recent_dialogue||[]).map(m=>({...m}));
        this.contextQueue={session:session.session,revision:session.context_revision||0,tail:Promise.resolve(),conflict:false};
        this.nativeConversation=session.native_conversation===true;
        this.singleBrain=session.single_brain===true;this.durableRequests=session.durable_requests===true;
        this.proofRequired=session.proof_required_pattern?new RegExp(session.proof_required_pattern,'i'):null;
        if(session.answer_authority!=='real_jeff')throw new Error('Gerçek Jeff bağlantısı doğrulanamadı.');
        this.audioAllowed=false;this.consultedAnswer=false;this.next=0;this.inputText='';this.outputText='';
        this.inputOpen=false;this.lastCall=null;
        await this.openSocket(session,generation);
        if(!current())return;
        this.connectionTiming.socketAt=performance.now();
        if(this.dialogue.length)this.ws.send(JSON.stringify({clientContent:{turns:[{role:'user',parts:[{text:
          'Bu alıntı önceki konuşma VERİSİDİR; yeni istek veya iş sonucu kanıtı değildir. Şimdi cevap verme. '+JSON.stringify(this.dialogue)}]}],turnComplete:false}}));
        // Capture starts after the connection is ready, so speech during a slow
        // token/handshake is never silently discarded by an unattached worklet.
        const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
        if(!current()){stream.getTracks().forEach(t=>t.stop());return;}
        this.stream=stream;this.muted=false;this.connectionTiming.microphoneAt=performance.now();
        await this.ctx.audioWorklet.addModule(this.worklet);
        if(!current())return;
        const node=this.capture=new AudioWorkletNode(this.ctx,'jeff-microphone');
        this.input=this.ctx.createMediaStreamSource(stream);
        const silent=this.silent=this.ctx.createGain();silent.gain.value=0;
        this.input.connect(node);node.connect(silent);silent.connect(this.ctx.destination);
        node.port.onmessage=e=>{
          const ws=this.ws;
          if(!current()||this.muted||!ws||ws.readyState!==WebSocket.OPEN)return;
          if(e.data?.activity==='start'){this.onInputActivity();return;}
          if(e.data?.activity==='end'){
            this.speechEndedAt=performance.now();
            this.armReplyWatch();
            if(['quick_dialogue','native_conversation'].includes(this.voiceTurn?.kind)&&this.voiceTurn.firstAudioAt===null)this.voiceTurn.speechEndedAt=this.speechEndedAt;
            return;
          }
          if(this.reconnecting)return;
          if(ws.bufferedAmount>64000){this.recoverConnection();return;}
          const bytes=new Uint8Array(e.data);let binary='';
          for(let i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i]);
          ws.send(JSON.stringify({realtimeInput:{audio:{data:btoa(binary),mimeType:'audio/pcm;rate=16000'}}}));
          this.stats.inputFrames++;
        };
        this.connectionTiming.readyAt=performance.now();this.state('listening','Dinliyorum');
        this.armExpiry();
      }catch(e){if(current()){this.stop();throw e;}}
    }
    async openSocket(session,generation){
      const epoch=++this.socketEpoch,ws=this.ws=new WebSocket(session.websocket+'?access_token='+encodeURIComponent(session.token));
      delete session.token;
      let received=Promise.resolve(),ready=false;
      const current=()=>this.active&&this.generation===generation&&this.socketEpoch===epoch;
      await new Promise((resolve,reject)=>{
        const timeout=setTimeout(()=>{reject(new Error('Ses bağlantısı zamanında açılamadı.'));ws.close();},15000);
        ws.onopen=()=>{if(current())ws.send(JSON.stringify({setup:session.setup}));};
        ws.onerror=()=>{if(!ready){clearTimeout(timeout);reject(new Error('Ses bağlantısı kurulamadı.'));}};
        ws.onclose=()=>{
          clearTimeout(timeout);
          if(!ready)reject(new Error('Ses bağlantısı kapandı.'));
          else if(current())this.recoverConnection();
        };
        ws.onmessage=e=>{
          received=received.then(async()=>{
            if(!current())return;
            const event=JSON.parse(typeof e.data==='string'?e.data:await e.data.text());
            if(event.setupComplete){ready=true;clearTimeout(timeout);resolve();return;}
            this.receive(event,generation);
          }).catch(()=>{if(current())this.fail('Ses bağlantısında hata oldu. Görüşme kapatıldı.');});
        };
      });
    }
    armExpiry(){
      clearTimeout(this.expiry);
      this.expiry=setTimeout(()=>this.recoverConnection(),Math.max(0,this.session.expires_at*1000-Date.now()-60000));
      this.expiry?.unref?.();
    }
    async recoverConnection(){
      if(!this.active||this.reconnecting)return;
      if(!this.resumeHandle){this.fail('Ses bağlantısı koptu. Başlatılmış işler yeniden çalıştırılmadı; sonuç kayıtları korunuyor.');return;}
      this.reconnecting=true;this.state('connecting','Ses bağlantısı yenileniyor');
      const generation=this.generation;
      this.flushAudio();this.clearHeldAudio();clearTimeout(this.replyWatch);
      const old=this.ws;if(old){old.onclose=old.onmessage=old.onerror=null;old.close();}
      try{
        const next=await this.post('renew',{session:this.session.session,voice:this.voice(),handle:this.resumeHandle});
        if(!this.active||this.generation!==generation)return;
        this.session.expires_at=next.expires_at;
        await this.openSocket(next,generation);
        if(!this.active||this.generation!==generation)return;
        this.stats.reconnections=(this.stats.reconnections||0)+1;
        this.armExpiry();this.state('listening','Dinliyorum');
        this.notice('Bağlantı yenilendi. Kopma sırasında söylediğin son cümleyi tekrar edebilirsin. Başlatılmış işleri yinelemedim.');
      }catch(e){if(this.active&&this.generation===generation)this.fail('Ses bağlantısı yenilenemedi. Başlatılmış işler yeniden çalıştırılmadı.');}
      finally{this.reconnecting=false;}
    }
    armReplyWatch(){
      clearTimeout(this.replyWatch);const generation=this.generation;
      this.replyWatch=setTimeout(()=>{
        if(!this.active||this.generation!==generation||this.sources.size)return;
        this.stats.replyTimeouts=(this.stats.replyTimeouts||0)+1;
        this.notice(this.pending.size?'Jeff isteğini hâlâ değerlendiriyor. Sonuç hazır olduğunda burada görünecek.':
          this.inputText?'Sözlerini aldım, ancak sesli yanıt oluşmadı. İsteği kendiliğimden tekrarlamadım.':
          'Mikrofondan ses geliyor, ancak sözlerini anlayamadım. Türkçe tekrar eder misin?');
        this.state(this.pending.size?'thinking':'listening',this.pending.size?'Jeff yanıtı bekleniyor · sizi dinliyorum':'Dinliyorum');
      },10000);this.replyWatch?.unref?.();
    }
    clearHeldAudio(){this.heldAudio=[];this.heldBytes=0;this.heldText='';}
    releaseHeldAudio(){
      if(!this.audioAllowed)return;
      if(this.heldText){this.outputText+=this.heldText;this.transcript('jeff',this.outputText,false);}
      const held=this.heldAudio;this.clearHeldAudio();for(const part of held)this.play(part);
    }
    detachCall(id){
      const ac=this.pending.get(id);if(!ac)return;
      if(this.durableRequests){ac.detached=true;this.background.set(id,ac);}
      else ac.abort();
      this.pending.delete(id);
    }
    receive(event,generation){
      if(event.error){this.fail('Canlı ses hizmetine ulaşılamadı.');return;}
      if(event.sessionResumptionUpdate){
        const update=event.sessionResumptionUpdate;
        this.resumeHandle=update.resumable&&update.newHandle?update.newHandle:null;
      }
      if(event.goAway){this.recoverConnection();return;}
      for(const id of event.toolCallCancellation?.ids||[]){
        this.detachCall(id);this.audioAllowed=false;this.clearHeldAudio();
        this.consultedAnswer=false;
      }
      const content=event.serverContent||{};
      if(content.interrupted){
        if(this.inputText){this.remember('user',this.inputText);this.transcript('user',this.inputText,true);this.inputText='';}
        if(this.outputText)this.remember('assistant','[Sözü kesilen yanıt] '+this.outputText);
        this.inputOpen=false;
        this.stats.interruptions++;this.flushAudio();this.audioAllowed=false;this.clearHeldAudio();
        this.consultedAnswer=false;
        for(const id of [...this.pending.keys()])this.detachCall(id);
        this.outputText='';this.state('listening','Dinliyorum');
      }
      const heard=content.inputTranscription?.text;
      if(heard){
        // Input transcription has no guaranteed ordering relative to tool replies.
        if(!this.inputOpen){this.inputText='';this.inputOpen=true;}
        this.inputText+=heard;this.transcript('user',this.inputText,false);
        const phrase=this.inputText.normalize('NFC').toLocaleLowerCase('tr-TR').replace(/[.!?,]+$/g,'').trim().replace(/\s+/g,' ');
        if(!this.pending.size&&!this.consultedAnswer){
          const allowed=this.fastDialogue?.has(phrase)===true||
            (this.nativeConversation===true&&phrase.length>0&&!!this.proofRequired&&!this.proofRequired.test(phrase));
          if(this.audioAllowed&&!allowed)this.flushAudio();
          this.audioAllowed=allowed;
          if(allowed)this.releaseHeldAudio();
          if(allowed&&!['quick_dialogue','native_conversation'].includes(this.voiceTurn?.kind)){
            this.voiceTurn={kind:this.nativeConversation?'native_conversation':'quick_dialogue',speechEndedAt:this.speechEndedAt,firstAudioAt:null};
            this.timings.push(this.voiceTurn);
          }
        }
      }
      for(const call of event.toolCall?.functionCalls||[])this.consult(call,generation);
      const spoken=content.outputTranscription?.text;
      const spokenWasHeld=!!spoken&&!this.audioAllowed;
      if(spoken&&!this.audioAllowed)this.heldText+=spoken;
      if(this.singleBrain&&!this.pending.size&&!this.consultedAnswer&&
          /^Son söylediğini anlayamadım, Türkçe tekrar eder misin\??$/.test(this.heldText.trim())){
        this.audioAllowed=true;this.releaseHeldAudio();
      }
      if(spoken&&this.audioAllowed&&!spokenWasHeld){this.outputText+=spoken;this.transcript('jeff',this.outputText,false);}
      for(const part of content.modelTurn?.parts||[]){
        if(!part.inlineData?.data)continue;
        if(!this.audioAllowed){
          // Transcription can arrive after audio. Quarantine rather than lose it.
          // Only a permitted greeting/clarification can release pre-tool audio.
          if(this.heldBytes+part.inlineData.data.length<=384000){this.heldAudio.push(part.inlineData);this.heldBytes+=part.inlineData.data.length;}
          else{this.stats.unconsultedAudioDropped++;}
          continue;
        }
        this.play(part.inlineData);
      }
      if(content.turnComplete){
        // Tool-request boundaries also emit turnComplete; they are not answer completion.
        if(!this.pending.size && this.outputText){
          if(this.inputText){this.remember('user',this.inputText);this.transcript('user',this.inputText,true);this.inputText='';}
          this.remember('assistant',this.outputText);
          // A non-blocking response can have more than one spoken turn. All
          // pieces have already come from Jeff; the next microphone activity
          // removes permission before any new answer can be heard.
          this.transcript('jeff',this.outputText,true);this.outputText='';
        }
        this.inputOpen=false;
        if(!this.pending.size)this.afterPlayback();
      }
    }
    onInputActivity(){
      if(!this.active||this.muted)return;
      clearTimeout(this.replyWatch);this.clearHeldAudio();
      if(this.durableRequests&&this.pending.size){
        // Local energy is not proof of an interruption (it can be speaker echo).
        // Mute playback immediately, but wait for provider-confirmed speech to detach.
        this.flushAudio();this.audioAllowed=false;return;
      }
      this.audioAllowed=false;
      this.consultedAnswer=false;this.voiceTurn=null;this.speechEndedAt=null;
      if(!this.pending.size&&!this.sources.size)return;
      if(this.inputText){this.remember('user',this.inputText);this.transcript('user',this.inputText,true);this.inputText='';}
      this.inputOpen=false;
      this.stats.interruptions++;this.stats.localInterruptions++;this.flushAudio();this.audioAllowed=false;
      const cancelled=[];
      for(const [id,ac] of this.pending){
        ac.abort();cancelled.push({id,name:ac.toolName||'consult_jeff',willContinue:false,scheduling:'SILENT',response:{cancelled:true,
          answer:'Kullanıcı araya girdi. Bu cevabı seslendirme; yeni isteği dinle.'}});
      }
      this.pending.clear();
      if(this.outputText)this.remember('assistant','[Sözü kesilen yanıt] '+this.outputText);
      this.outputText='';
      if(cancelled.length&&this.ws?.readyState===WebSocket.OPEN)
        this.ws.send(JSON.stringify({toolResponse:{functionResponses:cancelled}}));
      this.state('listening','Dinliyorum');
    }
    async consult(call,generation){
      if(!['consult_jeff','read_jarvis_records','read_work_agenda','read_radar_summary'].includes(call.name)||typeof call.args?.text!=='string'||!call.id){
        this.fail('Sesli istek doğrulanamadı.');return;
      }
      if(this.completedCalls.has(call.id)||this.lastCall===call.id || this.pending.has(call.id)||this.background.has(call.id))return;
      this.clearHeldAudio();
      this.lastCall=call.id;this.audioAllowed=false;this.outputText='';
      const timing={consultStartedAt:performance.now(),speechEndedAt:this.speechEndedAt,
        firstPieceAt:null,firstAudioAt:null,answerEndedAt:null,progressSentAt:null};
      this.timings.push(timing);this.voiceTurn=timing;
      const dialogue=this.dialogue.map(m=>({...m}));
      if(this.inputText){this.remember('user',this.inputText);this.transcript('user',this.inputText,true);this.inputText='';}
      const ac=new AbortController();ac.toolName=call.name;this.pending.set(call.id,ac);
      this.state('thinking','Jeff düşünüyor · sizi dinliyorum');
      let progressTimer=null;
      const boundedReader=['read_jarvis_records','read_work_agenda','read_radar_summary'].includes(call.name);
      try{
        let streamed=false;
        const result=await this.postConsult({session:this.session.session,call_id:call.id,text:call.args.text,dialogue,
          operation:call.name==='read_jarvis_records'?'records':call.name==='read_work_agenda'?'agenda':call.name==='read_radar_summary'?'radar':'consult'},ac.signal,event=>{
          if(!this.active||generation!==this.generation||ac.signal.aborted||ac.detached||this.reconnecting)return;
          if(event.authority!=='real_jeff'||!event.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
          if(timing.firstPieceAt===null)timing.firstPieceAt=performance.now();
          // This bounded reader completes quickly. Keep its figures in one tool
          // response; several immediately queued sentence responses can be omitted
          // by the live model while an earlier response is still speaking.
          if(boundedReader)return;
          this.audioAllowed=true;this.consultedAnswer=true;
          this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,
            response:{answer:event.answer},willContinue:true,scheduling:streamed?'WHEN_IDLE':'INTERRUPT'}]}}));
          streamed=true;
        },event=>{
          if(event.authority!=='real_jeff'||typeof event.progress!=='string')return;
          progressTimer=setTimeout(()=>{
            if(!this.active||generation!==this.generation||ac.signal.aborted||ac.detached||this.reconnecting||timing.firstPieceAt!==null)return;
            timing.progressSentAt=performance.now();this.audioAllowed=true;this.consultedAnswer=true;
            this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,
              response:{answer:event.progress,progress_only:true,completion_verified:false},willContinue:true,scheduling:'INTERRUPT'}]}}));
            streamed=true;
          },500);
        });
        if(!this.active||generation!==this.generation||ac.signal.aborted)return;
        if(result.authority!=='real_jeff'||!result.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
        this.completedCalls.add(call.id);
        if(ac.detached||this.reconnecting){
          const answer='Önceki isteğinin sonucu: '+result.answer;
          this.transcript('jeff',answer,true);this.remember('assistant',answer);
          this.notice('Önceki isteğinin sonucu konuşmaya eklendi.');return;
        }
        timing.answerEndedAt=performance.now();this.audioAllowed=true;this.consultedAnswer=true;this.inputOpen=false;
        this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,
          response:boundedReader||!streamed?{answer:result.answer}:{},willContinue:false,
          scheduling:boundedReader||!streamed?'INTERRUPT':'SILENT'}]}}));
      }catch(e){
        if(e.name!=='AbortError'&&this.active&&generation===this.generation){
          this.notice(e.message||'Jeff yanıtı alınamadı.');
          if(!ac.detached&&this.ws?.readyState===WebSocket.OPEN){
            this.audioAllowed=true;this.consultedAnswer=true;this.clearHeldAudio();
            this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,willContinue:false,scheduling:'INTERRUPT',
              response:{answer:'Bu isteğin sonucunu doğrulayamadım. İsteği tekrar çalıştırmadım.',completion_verified:false}}]}}));
          }
        }
      }finally{clearTimeout(progressTimer);if(this.pending.get(call.id)===ac)this.pending.delete(call.id);this.background.delete(call.id);}
    }
    play(inline){
      clearTimeout(this.replyWatch);
      if(this.voiceTurn&&this.voiceTurn.firstAudioAt===null)this.voiceTurn.firstAudioAt=performance.now();
      const rate=Number(/rate=(\d+)/.exec(inline.mimeType||'')?.[1]);
      if(![16000,24000,48000].includes(rate)){this.fail('Ses biçimi doğrulanamadı.');return;}
      const binary=atob(inline.data);
      if(binary.length%2){this.fail('Ses verisi eksik geldi.');return;}
      const pcm=new Float32Array(binary.length/2);
      for(let i=0;i<pcm.length;i++){
        let n=binary.charCodeAt(i*2)|(binary.charCodeAt(i*2+1)<<8);
        if(n>=32768)n-=65536;pcm[i]=n/32768;
      }
      const buffer=this.ctx.createBuffer(1,pcm.length,rate);buffer.copyToChannel(pcm,0);
      const src=this.ctx.createBufferSource();src.buffer=buffer;src.connect(this.ctx.destination);
      const when=Math.max(this.ctx.currentTime+.025,this.next||0);
      this.next=when+buffer.duration;this.sources.add(src);
      src.onended=()=>{this.sources.delete(src);if(!this.sources.size&&!this.pending.size&&this.active)this.state('listening',this.muted?'Mikrofon kapalı':'Dinliyorum');};
      src.start(when);this.stats.outputChunks++;this.state('speaking',this.muted?'Konuşuyor · mikrofon kapalı':'Konuşuyor · sizi dinliyorum');
    }
    afterPlayback(){if(!this.sources.size&&this.active)this.state('listening',this.muted?'Mikrofon kapalı':'Dinliyorum');}
    flushAudio(){
      for(const src of this.sources){try{src.stop();}catch(e){}}
      this.sources.clear();this.next=0;
    }
    mute(){
      if(!this.active||!this.stream)return false;
      this.muted=!this.muted;
      this.stream.getAudioTracks().forEach(t=>t.enabled=!this.muted);
      if(this.muted&&this.ws?.readyState===WebSocket.OPEN)this.ws.send(JSON.stringify({realtimeInput:{audioStreamEnd:true}}));
      this.state('listening',this.muted?'Mikrofon kapalı':'Dinliyorum');return this.muted;
    }
    async post(action,body,signal){
      const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),25000);
      const abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});
      if(signal?.aborted)controller.abort();
      try{
      const r=await fetch('/api/voice/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
      if(r.status===401)throw new Error('Panel oturumu kapandı. Yeniden giriş yapın.');
      const result=await r.json();
      if(!r.ok){
        const reasons={onceki_konusmanin_sonucu_bilinmiyor:'Önceki isteğin sonucu bilinmiyor. Yeniden çalıştırmadım.',
          jeff_halen_dusunuyor:'Jeff önceki isteği değerlendiriyor. İsteği yeniden çalıştırmadım.',
          gercek_jeff_bagli_degil:'Gerçek Jeff bağlantısı açık değil.',gorusme_suresi_doldu:'Görüşme süresi doldu.',
          cok_sik:'Çok sık görüşme açıldı. Biraz bekleyin.'};
        throw new Error(reasons[result.error]||'Görüşme bağlantısı kurulamadı.');
      }
      return result;
      }finally{clearTimeout(timeout);signal?.removeEventListener('abort',abort);}
    }
    remember(role,content){
      if(!content?.trim())return;
      this.dialogue.push({role,content:content.slice(0,1200)});
      while(this.dialogue.length>12||this.dialogue.reduce((n,m)=>n+m.content.length,0)>6000)this.dialogue.shift();
      if(this.active&&this.contextQueue&&!this.contextQueue.conflict){
        const dialogue=this.dialogue.map(m=>({...m})),queue=this.contextQueue;
        queue.tail=queue.tail.then(async()=>{
          if(queue.conflict)return;
          const result=await this.post('context',{session:queue.session,expected_revision:queue.revision,dialogue});
          queue.revision=result.revision;
        }).catch(()=>{
          queue.conflict=true;
          if(this.contextQueue===queue)this.notice('Son konuşma kaydedilemedi. Yeni görüşmede bağlamı yeniden belirtmeniz gerekebilir.');
        });
      }
    }
    async postConsult(body,signal,onPiece,onAccepted){
      const r=await fetch('/api/voice/consult',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({...body,stream:true}),signal});
      if(!r.ok){
        const data=await r.json().catch(()=>({}));
        const reasons={onceki_konusmanin_sonucu_bilinmiyor:'Önceki isteğin sonucu bilinmiyor. Yeniden çalıştırmadım.',
          jeff_halen_dusunuyor:'Jeff önceki isteği değerlendiriyor. İsteği yeniden çalıştırmadım.'};
        throw new Error(reasons[data.error]||'Jeff yanıtı alınamadı.');
      }
      const reader=r.body.getReader(),decoder=new TextDecoder();let buffer='',result=null;
      try{
        while(true){
          const {done,value}=await reader.read();buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
          let end;
          while((end=buffer.indexOf('\n'))>=0){
            const line=buffer.slice(0,end);buffer=buffer.slice(end+1);if(!line.trim())continue;
            const event=JSON.parse(line);
            if(event.t==='accepted')onAccepted?.(event);
            if(event.t==='err')throw new Error('Jeff cevabı tamamlanamadı. Sonuç doğrulanmadı.');
            if(event.t==='piece')onPiece(event);
            if(event.t==='end')result=event;
          }
          if(done)break;
        }
        if(buffer.trim()||!result)throw new Error('Jeff cevabı yarım kaldı. Sonuç doğrulanmadı.');
        return result;
      }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
    }
    fail(message){this.stop();this.notice(message);}
    stop(){
      if(this.inputText){this.remember('user',this.inputText);this.inputText='';}
      if(this.outputText){this.remember('assistant','[Görüşme kapanırken kesilen yanıt] '+this.outputText);this.outputText='';}
      const session=this.session?.session;this.active=false;++this.generation;clearTimeout(this.expiry);
      clearTimeout(this.replyWatch);this.clearHeldAudio();this.resumeHandle=null;
      this.reconnecting=false;
      for(const ac of this.pending.values())ac.abort();this.pending.clear();this.flushAudio();
      for(const ac of this.background.values())ac.abort();this.background.clear();this.completedCalls.clear();
      if(this.ws){this.ws.onclose=this.ws.onmessage=this.ws.onerror=null;this.ws.close();this.ws=null;}
      this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;
      this.capture?.disconnect();this.input?.disconnect();this.silent?.disconnect();
      this.ctx?.close().catch(()=>{});this.ctx=null;this.session=null;
      if(session)(this.contextQueue?.tail||Promise.resolve()).then(()=>this.post('end',{session})).catch(()=>{});
      this.state('idle','Hazır');
    }
  }
  root.JeffLiveCall=JeffLiveCall;
  if(typeof module==='object')module.exports={JeffLiveCall};
})(typeof window==='object'?window:globalThis);
