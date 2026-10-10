/* One continuous, interruptible call. No recognition restart or per-turn send button. */
(function(root){
  class JeffLiveCall {
    constructor({state,transcript,notice,voice,worklet,routeUtterances=true,opportunity=()=>null}){
      Object.assign(this,{state,transcript,notice,voice,worklet,opportunity});
      this.active=false; this.generation=0; this.sources=new Set(); this.pending=new Map();
      this.stats={inputFrames:0,outputChunks:0,interruptions:0,localInterruptions:0,unconsultedAudioDropped:0};
      this.timings=[];this.speechEndedAt=null;this.voiceTurn=null;
      this.dialogue=[];
      this.inputText='';this.outputText='';
      this.heldAudio=[];this.heldBytes=0;this.heldText='';this.completedCalls=new Set();
      this.background=new Map();this.resultAnnouncements=[];this.socketEpoch=0;
      this.inputActive=false;this.lastInputAt=0;
      this.replyReceived=false;
      this.callResults=new Map();this.inputCommitted=false;this.canonicalOutput=false;this.answerCall=null;
      this.turnOutcomes=new Map();
      this.routeUtterances=routeUtterances;this.utterance=null;this.utteranceCounter=0;
      this.unboundCalls=[];this.providerBindings=new Map();this.brainQueue=Promise.resolve();
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
        this.inputCommitted=false;this.canonicalOutput=false;this.answerCall=null;
        this.turnOutcomes.clear();
        this.utterance=null;this.unboundCalls=[];this.providerBindings.clear();this.brainQueue=Promise.resolve();
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
            this.inputActive=false;this.lastInputAt=performance.now();
            this.speechEndedAt=performance.now();
            this.armReplyWatch();
            if(this.routeUtterances)this.scheduleUtterance();
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
      // A resumed socket has a different provider tool context. Keep accepted
      // work alive, but deliver its canonical result rather than an old tool ID.
      for(const [id,ac] of this.pending){ac.detached=true;this.background.set(id,ac);}
      this.pending.clear();
      this.announcement?.abort();
      this.flushAudio();this.clearHeldAudio();clearTimeout(this.replyWatch);
      const old=this.ws;if(old){old.onclose=old.onmessage=old.onerror=null;old.close();}
      try{
        for(let attempt=0;attempt<3;attempt++){
          if(!this.active||this.generation!==generation)return;
          try{
            const next=await this.post('renew',{session:this.session.session,voice:this.voice(),handle:this.resumeHandle});
            if(!this.active||this.generation!==generation)return;
            this.session.expires_at=next.expires_at;
            await this.openSocket(next,generation);break;
          }catch(e){
            if((e.status&&e.status<500)||attempt===2)throw e;
            if(!this.active||this.generation!==generation)return;
            const failed=this.ws;if(failed){failed.onclose=failed.onmessage=failed.onerror=null;failed.close();}
            await new Promise(resolve=>setTimeout(resolve,400*(attempt+1)));
          }
        }
        if(!this.active||this.generation!==generation)return;
        this.stats.reconnections=(this.stats.reconnections||0)+1;
        this.armExpiry();this.state('listening','Dinliyorum');
        this.notice('Bağlantı yenilendi. Kopma sırasında söylediğin son cümleyi tekrar edebilirsin. Başlatılmış işleri yinelemedim.');
      }catch(e){if(this.active&&this.generation===generation)this.fail('Ses bağlantısı yenilenemedi. Başlatılmış işler yeniden çalıştırılmadı.');}
      finally{this.reconnecting=false;}
    }
    armReplyWatch(){
      clearTimeout(this.replyWatch);const generation=this.generation;
      if(this.replyReceived)return;
      this.replyWatch=setTimeout(()=>{
        if(!this.active||this.generation!==generation||this.sources.size)return;
        this.stats.replyTimeouts=(this.stats.replyTimeouts||0)+1;
        const waiting=this.pending.size||this.background.size;
        this.notice(waiting?'Jeff isteğini hâlâ değerlendiriyor. Sonuç hazır olduğunda burada görünecek.':
          this.inputText?'Sözlerini aldım, ancak sesli yanıt oluşmadı. İsteği kendiliğimden tekrarlamadım.':
          'Mikrofondan ses geliyor, ancak sözlerini anlayamadım. Türkçe tekrar eder misin?');
        this.state(waiting?'thinking':'listening',waiting?'Jeff yanıtı bekleniyor · sizi dinliyorum':'Dinliyorum');
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
        const bound=this.providerBindings.get(id);
        if(bound)for(const call of bound.calls)if(call.id===id)call.cancelled=true;
        this.detachCall(id);this.audioAllowed=false;this.clearHeldAudio();
        this.consultedAnswer=false;
      }
      const content=event.serverContent||{};
      if(content.interrupted){
        this.announcement?.abort();
        if(this.inputText&&!this.routeUtterances){this.commitInput();this.transcript('user',this.inputText,true);this.inputText='';}
        if(this.outputText&&!this.canonicalOutput)this.remember('assistant','[Sözü kesilen yanıt] '+this.outputText);
        this.answerCall=null;this.inputCommitted=false;this.canonicalOutput=false;
        this.turnOutcomes.clear();
        if(!this.routeUtterances)this.inputOpen=false;
        this.stats.interruptions++;this.flushAudio();this.audioAllowed=false;this.clearHeldAudio();
        this.consultedAnswer=false;
        for(const id of [...this.pending.keys()])this.detachCall(id);
        this.outputText='';this.state('listening','Dinliyorum');
      }
      let heard=content.inputTranscription?.text;
      // A repeated full transcript while canonical speech is still outstanding
      // does not authorize another execution. Local new-speech activity clears
      // the previous utterance; a genuinely different recognized question can
      // proceed without waiting for speech to finish.
      if(heard&&this.routeUtterances&&!this.inputOpen&&this.utterance?.done&&this.answerCall?.awaiting){
        const normalize=text=>text.normalize('NFC').toLocaleLowerCase('tr-TR').trim().replace(/\s+/g,' ').replace(/[.!?]+$/g,'');
        const fragment=normalize(heard),previous=normalize(this.utterance.text);
        if(fragment&&(fragment===previous||previous.endsWith(' '+fragment))){
          heard='';this.stats.completedTranscriptsSuppressed=(this.stats.completedTranscriptsSuppressed||0)+1;
        }
      }
      if(heard){
        // Input transcription has no guaranteed ordering relative to tool replies.
        if(!this.inputOpen){
          if(this.routeUtterances&&this.utterance?.done)this.utterance=null;
          this.inputText='';this.inputOpen=true;
          // Local VAD can miss quiet speech. A fresh provider utterance must not
          // inherit the previous answer's permission, even without local activity.
          // Late transcription of an outstanding tool turn is still that same turn.
          if(!this.pending.size&&!this.answerCall?.awaiting){
            const previousAnswer=this.consultedAnswer||this.canonicalOutput;
            this.audioAllowed=false;this.consultedAnswer=false;
            this.inputCommitted=false;this.canonicalOutput=false;if(previousAnswer)this.clearHeldAudio();
            this.turnOutcomes.clear();
          }
        }
        this.inputText+=heard;this.transcript('user',this.inputText,false);
        if(this.routeUtterances){
          if(!this.utterance){
            this.utterance={text:this.inputText,calls:this.unboundCalls.splice(0),dispatched:false,opportunityId:this.opportunity()};
            for(const call of this.utterance.calls)this.providerBindings.set(call.id,this.utterance);
          }else if(!this.utterance.dispatched)this.utterance.text=this.inputText;
          this.scheduleUtterance();
        }
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
      for(const call of event.toolCall?.functionCalls||[]){
        if(this.routeUtterances)this.bindProviderCall(call);
        else this.consult(call,generation);
      }
      const spoken=content.outputTranscription?.text;
      const spokenWasHeld=!!spoken&&!this.audioAllowed;
      if(spoken&&!this.audioAllowed&&!this.canonicalOutput&&!this.routeUtterances)this.heldText+=spoken;
      if(this.singleBrain&&!this.pending.size&&!this.consultedAnswer&&
          /^Son söylediğini anlayamadım, Türkçe tekrar eder misin\??$/.test(this.heldText.trim())){
        this.audioAllowed=true;this.releaseHeldAudio();
      }
      if(spoken&&this.audioAllowed&&!this.canonicalOutput&&!this.routeUtterances&&!spokenWasHeld){this.outputText+=spoken;this.transcript('jeff',this.outputText,false);}
      for(const part of content.modelTurn?.parts||[]){
        if(!part.inlineData?.data)continue;
        // A tool result can cause the native model to paraphrase, invent a cached
        // answer or speak despite SILENT scheduling. Only canonical Jeff TTS is
        // authorized during a consulted turn, including unknown-outcome errors.
        if(this.canonicalOutput||this.routeUtterances){this.stats.unconsultedAudioDropped++;continue;}
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
          clearTimeout(this.replyWatch);
          if(this.inputText){this.commitInput();this.transcript('user',this.inputText,true);this.inputText='';}
          if(!this.canonicalOutput)this.remember('assistant',this.outputText);
          // A non-blocking response can have more than one spoken turn. All
          // pieces have already come from Jeff; the next microphone activity
          // removes permission before any new answer can be heard.
          this.transcript('jeff',this.outputText,true);this.outputText='';
          if(this.answerCall)this.answerCall.awaiting=false;
        }
        if(!this.routeUtterances)this.inputOpen=false;
        if(!this.pending.size)this.afterPlayback();
      }
    }
    onInputActivity(){
      if(!this.active||this.muted)return;
      this.replyReceived=false;
      clearTimeout(this.utteranceTimer);
      if(this.routeUtterances&&this.utterance?.dispatched){
        this.utterance=null;this.inputText='';this.inputOpen=false;
      }
      this.inputActive=true;this.lastInputAt=performance.now();this.announcement?.abort();
      clearTimeout(this.replyWatch);this.clearHeldAudio();
      if(this.durableRequests&&this.pending.size){
        // Local energy is not proof of an interruption (it can be speaker echo).
        // Mute playback immediately, but wait for provider-confirmed speech to detach.
        this.flushAudio();this.audioAllowed=false;return;
      }
      this.audioAllowed=false;
      this.consultedAnswer=false;this.voiceTurn=null;this.speechEndedAt=null;
      this.answerCall=null;
      if(!this.pending.size&&!this.sources.size){this.inputCommitted=false;this.canonicalOutput=false;this.turnOutcomes.clear();return;}
      if(this.inputText){this.commitInput();this.transcript('user',this.inputText,true);this.inputText='';}
      this.inputOpen=false;
      this.stats.interruptions++;this.stats.localInterruptions++;this.flushAudio();this.audioAllowed=false;
      const cancelled=[];
      for(const [id,ac] of this.pending){
        ac.abort();cancelled.push({id,name:ac.toolName||'consult_jeff',response:{cancelled:true,scheduling:'SILENT',
          answer:'Kullanıcı araya girdi. Bu cevabı seslendirme; yeni isteği dinle.'}});
      }
      this.pending.clear();
      if(this.outputText&&!this.canonicalOutput)this.remember('assistant','[Sözü kesilen yanıt] '+this.outputText);
      this.outputText='';
      this.inputCommitted=false;this.canonicalOutput=false;
      this.turnOutcomes.clear();
      if(cancelled.length&&this.ws?.readyState===WebSocket.OPEN)
        this.ws.send(JSON.stringify({toolResponse:{functionResponses:cancelled}}));
      this.state('listening','Dinliyorum');
    }
    bindProviderCall(call){
      if(!call.id||!['consult_jeff','read_jarvis_records','read_work_agenda','read_radar_summary'].includes(call.name)){
        this.fail('Sesli istek doğrulanamadı.');return;
      }
      call.boundEpoch=this.socketEpoch;
      const bound=this.providerBindings.get(call.id);
      if(bound){
        if(bound.result)this.sendProviderResult(call,bound.result,'SILENT');
        else if(!bound.calls.some(c=>c.id===call.id&&c.boundEpoch===call.boundEpoch))bound.calls.push(call);
        return;
      }
      const utterance=this.utterance;
      if(!utterance){this.unboundCalls.push(call);return;}
      this.providerBindings.set(call.id,utterance);utterance.calls.push(call);
      if(utterance.result)this.sendProviderResult(call,utterance.result,'SILENT');
      // A native model tool decision is only a transport binding. It cannot
      // submit, rewrite or replay the user's request. The transcript does that.
    }
    scheduleUtterance(){
      clearTimeout(this.utteranceTimer);
      const utterance=this.utterance,generation=this.generation;
      if(!utterance||utterance.dispatched||!utterance.text?.trim())return;
      this.utteranceTimer=setTimeout(()=>{
        if(!this.active||generation!==this.generation||this.utterance!==utterance)return;
        if(this.inputActive){this.scheduleUtterance();return;}
        this.dispatchUtterance(utterance,generation);
      },700);this.utteranceTimer?.unref?.();
    }
    dispatchUtterance(utterance,generation){
      if(utterance.dispatched)return utterance.task;
      utterance.dispatched=true;
      const text=utterance.text.trim(),clean=text.normalize('NFC').toLocaleLowerCase('tr-TR').replace(/[.!?,]+$/g,'').trim();
      this.transcript('user',text,true);
      if(this.utterance===utterance){this.inputText='';this.inputOpen=false;}
      if(this.fastDialogue?.has(clean)){
        this.remember('user',text);this.inputCommitted=true;
        const answer=/teşekkür/u.test(clean)?'Rica ederim Bilal.':/duyuyor/u.test(clean)?'Sözlerini alıyorum Bilal.':'Buradayım Bilal, seni dinliyorum.';
        utterance.result={answer};utterance.done=true;this.remember('assistant',answer);
        for(const providerCall of utterance.calls)this.sendProviderResult(providerCall,utterance.result,'SILENT');
        this.transcript('jeff',answer,true);this.enqueueResultSpeech(answer,generation);return Promise.resolve();
      }
      // These are infrastructure-only reads of existing records. All other
      // requests go to the same unrestricted Hermes Jeff and his existing tools.
      const action=/\b(tara|başlat\w*|çalıştır\w*|yenile\w*|yap|aç|gönder\w*|sil\w*|öde\w*)\b/u;
      let name='consult_jeff';
      if(/^(?:(?:jeff\s+)?(?:ne iş var|bugün ne var|bekleyen iş var mı|işler ne durumda)(?:\s+jeff)?)$/u.test(clean))name='read_work_agenda';
      else if(/\b(haber\w*|radar\w*)\b/u.test(clean)&&/özet|durum|bitti|sonuç|neler|ne var|oku|anlat|rapor/u.test(clean)&&!action.test(clean))name='read_radar_summary';
      else if(/^(?:pablo ne durumda|pablo kaç açık iş var|onay bekleyen var mı|bekleyen onay var mı)$/u.test(clean))name='read_jarvis_records';
      const call={id:'jeff-utterance-'+(++this.utteranceCounter)+'-'+Math.random().toString(36).slice(2),
        name,args:{text},clientManaged:true,utterance};
      const execute=async()=>{
        if(!this.active||generation!==this.generation)return;
        // Capture context when this question starts, after the preceding Jeff
        // answer has completed. A queued follow-up must include that answer.
        utterance.dialogue=this.dialogue.map(m=>({...m}));
        this.remember('user',text);this.inputCommitted=true;
        try{await this.consult(call,generation);}finally{utterance.done=true;}
      };
      // Long Jeff consultations are serialised; speaking again does not turn
      // an admitted job into a second execution or a competing core request.
      utterance.task=name==='consult_jeff'?this.brainQueue.then(execute):execute();
      if(name==='consult_jeff')this.brainQueue=utterance.task.catch(()=>{});
      return utterance.task;
    }
    async consult(call,generation){
      if(!['consult_jeff','read_jarvis_records','read_work_agenda','read_radar_summary'].includes(call.name)||typeof call.args?.text!=='string'||!call.id){
        this.fail('Sesli istek doğrulanamadı.');return;
      }
      const opportunityId=call.clientManaged?call.utterance.opportunityId:this.opportunity();
      const requestKey=call.name+'|'+call.args.text.normalize('NFC').toLocaleLowerCase('tr-TR').trim().replace(/\s+/g,' ')+(opportunityId?'|'+opportunityId:'');
      const completed=this.callResults.get(call.id);
      if(completed){
        if(completed.requestKey===requestKey)this.sendToolResult(call,completed.response,'SILENT');
        else this.sendToolResult(call,{answer:'Bu istek kimliği önceki soruyla uyuşmuyor. Yeni iş çalıştırmadım.',completion_verified:false},'WHEN_IDLE');
        return;
      }
      const previousOutcome=!call.clientManaged&&this.turnOutcomes.get(requestKey);
      const unknownOutcome=!call.clientManaged&&[...this.turnOutcomes.values()].find(r=>r.completion_verified===false);
      if(previousOutcome||unknownOutcome){
        // A provider retry with a new ID is still the same user utterance.
        // In particular, an unknown outcome cannot authorize another execution.
        const response=previousOutcome||unknownOutcome;
        this.callResults.set(call.id,{requestKey,response});
        this.completedCalls.add(call.id);this.sendToolResult(call,response,'SILENT');return;
      }
      if(this.completedCalls.has(call.id)||this.lastCall===call.id || this.pending.has(call.id)||this.background.has(call.id))return;
      const equivalent=[...this.pending.values(),...this.background.values()].find(ac=>ac.requestKey===requestKey&&!ac.signal.aborted);
      if(equivalent){
        this.completedCalls.add(call.id);this.stats.duplicateRequestsSuppressed=(this.stats.duplicateRequestsSuppressed||0)+1;
        this.sendToolResult(call,{status:'already_running',answer:'Aynı isteğin asıl çağrısı sürüyor. Yeni bir istek açma; onun sonucunu bekle.'},'SILENT');
        return;
      }
      this.clearHeldAudio();
      this.lastCall=call.id;this.audioAllowed=false;this.outputText='';this.canonicalOutput=true;
      const timing={consultStartedAt:performance.now(),speechEndedAt:this.speechEndedAt,
        firstPieceAt:null,firstAudioAt:null,answerEndedAt:null,progressSentAt:null};
      this.timings.push(timing);this.voiceTurn=timing;
      const dialogue=call.clientManaged?call.utterance.dialogue:this.dialogue.map(m=>({...m}));
      if(!call.clientManaged){
        this.commitInput(call.args.text);
        if(this.inputText){this.transcript('user',this.inputText,true);this.inputText='';}
      }
      const ac=new AbortController();ac.toolName=call.name;ac.requestKey=requestKey;this.pending.set(call.id,ac);
      this.state('thinking','Jeff düşünüyor · sizi dinliyorum');
      try{
        const result=await this.postConsult({session:this.session.session,call_id:call.id,text:call.args.text,dialogue,
          ...(opportunityId?{opportunity_id:opportunityId}:{}),
          operation:call.name==='read_jarvis_records'?'records':call.name==='read_work_agenda'?'agenda':call.name==='read_radar_summary'?'radar':'consult'},ac.signal,event=>{
          if(!this.active||generation!==this.generation||ac.signal.aborted||ac.detached||this.reconnecting)return;
          if(event.authority!=='real_jeff'||!event.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
          if(timing.firstPieceAt===null)timing.firstPieceAt=performance.now();
          // Pipecat's Gemini adapter sends one complete FunctionResponse per call.
          // Partial SSE sentences are transport progress, not new tool completions.
        },event=>{
          if(event.authority!=='real_jeff'||typeof event.progress!=='string')return;
          timing.progressShownAt=performance.now();this.notice(event.progress);
        });
        if(!this.active||generation!==this.generation||ac.signal.aborted)return;
        if(result.authority!=='real_jeff'||!result.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
        this.completedCalls.add(call.id);
        this.callResults.set(call.id,{requestKey,response:{answer:result.answer}});
        this.turnOutcomes.set(requestKey,{answer:result.answer});
        if(ac.detached||this.reconnecting){
          if(call.clientManaged)this.sendToolResult(call,{answer:result.answer},'SILENT');
          const answer='Önceki isteğinin sonucu: '+result.answer;
          this.transcript('jeff',answer,true);this.remember('assistant',answer);
          this.notice('Önceki isteğinin sonucu konuşmaya eklendi.');
          this.enqueueResultSpeech(answer,generation);return;
        }
        timing.answerEndedAt=performance.now();this.audioAllowed=false;this.consultedAnswer=true;this.inputOpen=false;
        // The canonical Jeff answer, not the voice model's paraphrase or filler,
        // is the context bridge for the next user question.
        this.remember('assistant',result.answer);this.canonicalOutput=true;
        this.answerCall={id:call.id,text:call.args.text,awaiting:true};
        this.transcript('jeff',result.answer,true);
        this.sendToolResult(call,{answer:result.answer},'SILENT');
        this.enqueueResultSpeech(result.answer,generation);
      }catch(e){
        if(e.name!=='AbortError'&&this.active&&generation===this.generation){
          this.notice(e.message||'Jeff yanıtı alınamadı.');
          const response={answer:e.reason==='ses_model_hakki_dolu'
            ? 'Jeff’in cevap üreten bağlantılarındaki kullanım hakkı dolu. Bu soruyu işleme başlatmadım. Mevcut haberleri ve iş listesini okuyabilirim.'
            : 'Bu isteğin sonucunu doğrulayamadım. İsteği tekrar çalıştırmadım.',completion_verified:false};
          this.completedCalls.add(call.id);this.callResults.set(call.id,{requestKey,response});
          this.turnOutcomes.set(requestKey,response);
          this.remember('assistant',response.answer);
          if(!ac.detached&&this.ws?.readyState===WebSocket.OPEN){
            this.audioAllowed=false;this.consultedAnswer=true;this.canonicalOutput=true;this.clearHeldAudio();
            this.transcript('jeff',response.answer,true);
            this.sendToolResult(call,response,'SILENT');
            this.enqueueResultSpeech(response.answer,generation);
          }
        }
      }finally{if(this.pending.get(call.id)===ac)this.pending.delete(call.id);this.background.delete(call.id);}
    }
    sendToolResult(call,response,scheduling){
      // Gemini 3.8 reads scheduling inside response. No legacy willContinue or
      // scheduling fields are placed on FunctionResponse itself.
      if(call.clientManaged){
        call.utterance.result=response;
        for(const providerCall of call.utterance.calls)this.sendProviderResult(providerCall,response,scheduling);
      }else this.sendProviderResult(call,response,scheduling);
    }
    sendProviderResult(call,response,scheduling){
      if(call.cancelled||(call.boundEpoch!==undefined&&call.boundEpoch!==this.socketEpoch))return;
      if(!this.active||!this.ws)return;
      this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,response:{...response,scheduling}}]}}));
    }
    commitInput(fallback){
      if(this.inputCommitted)return;
      const text=this.inputText||fallback;
      if(text?.trim()){this.remember('user',text);this.inputCommitted=true;}
    }
    enqueueResultSpeech(answer,generation){
      // The current question has a canonical answer. Waiting for its PCM audio
      // cannot mean that Turkish recognition failed. An older detached answer
      // must not clear the watchdog of a newer unanswered human utterance.
      if(this.routeUtterances&&this.utterance?.result?.answer===answer)clearTimeout(this.replyWatch);
      this.resultAnnouncements.push({answer,generation,callId:this.answerCall?.id});
      this.scheduleResultSpeech();
    }
    scheduleResultSpeech(){
      clearTimeout(this.announcementTimer);
      if(!this.active||!this.resultAnnouncements.length)return;
      this.announcementTimer=setTimeout(()=>this.drainResultSpeech(),1000);this.announcementTimer?.unref?.();
    }
    async drainResultSpeech(){
      if(!this.active||this.announcement||!this.resultAnnouncements.length)return;
      if(this.reconnecting||this.inputActive||this.pending.size||this.sources.size||performance.now()-this.lastInputAt<750){
        this.scheduleResultSpeech();return;
      }
      const item=this.resultAnnouncements.shift();if(item.generation!==this.generation){this.scheduleResultSpeech();return;}
      const ac=this.announcement=new AbortController();
      try{await this.streamCanonicalSpeech(item.answer,ac.signal,item.generation);}
      catch(e){if(e.name!=='AbortError'&&this.active)this.notice('Sonuç konuşmaya yazıldı, ancak seslendirilemedi. İş tekrar çalıştırılmadı.');}
      finally{if(this.announcement===ac)this.announcement=null;if(this.answerCall&&this.answerCall.id===item.callId)this.answerCall.awaiting=false;this.scheduleResultSpeech();}
    }
    async streamCanonicalSpeech(answer,signal,generation){
      // Speak the journalled answer directly; no second agent can rewrite it.
      // The existing speech endpoint accepts at most 700 characters per request.
      const chunks=[];let rest=answer;
      while(rest.length){let end=Math.min(650,rest.length);if(end<rest.length){const space=rest.lastIndexOf(' ',end);if(space>0)end=space+1;}chunks.push(rest.slice(0,end));rest=rest.slice(end);}
      let started=false;
      for(const text of chunks){
        if(signal.aborted||this.reconnecting||!this.active||generation!==this.generation)return;
        const controller=new AbortController(),abort=()=>controller.abort();signal.addEventListener('abort',abort,{once:true});
        const timeout=setTimeout(abort,30000);let reader;
        try{
          const response=await fetch('/api/tts/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,voice:this.voice()}),signal:controller.signal});
          if(!response.ok||Number(response.headers.get('X-Sample-Rate'))!==24000)throw new Error('result_speech_unavailable');
          reader=response.body.getReader();let carry=new Uint8Array(0);
          while(true){
            const {done,value}=await reader.read();if(done){if(carry.length)throw new Error('incomplete_result_audio');break;}
            if(signal.aborted||this.reconnecting||!this.active||generation!==this.generation)return;
            const bytes=new Uint8Array(carry.length+value.length);bytes.set(carry);bytes.set(value,carry.length);
            const even=bytes.length-bytes.length%2;carry=bytes.slice(even);if(!even)continue;
            let raw='';for(let i=0;i<even;i++)raw+=String.fromCharCode(bytes[i]);
            if(!started){started=true;this.stats.backgroundSpeechStarted=(this.stats.backgroundSpeechStarted||0)+1;}
            this.play({data:btoa(raw),mimeType:'audio/pcm;rate=24000'});
          }
        }finally{clearTimeout(timeout);signal.removeEventListener('abort',abort);if(reader){await reader.cancel().catch(()=>{});reader.releaseLock();}}
      }
    }
    play(inline){
      this.replyReceived=true;
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
      if(this.muted){this.inputActive=false;this.lastInputAt=performance.now();}
      this.stream.getAudioTracks().forEach(t=>t.enabled=!this.muted);
      if(this.muted&&this.ws?.readyState===WebSocket.OPEN)this.ws.send(JSON.stringify({realtimeInput:{audioStreamEnd:true}}));
      this.state('listening',this.muted?'Mikrofon kapalı':'Dinliyorum');return this.muted;
    }
    async post(action,body,signal){
      const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),['renew','result'].includes(action)?10000:25000);
      const abort=()=>controller.abort();signal?.addEventListener('abort',abort,{once:true});
      if(signal?.aborted)controller.abort();
      try{
      const r=await fetch('/api/voice/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:controller.signal});
      if(r.status===401)throw Object.assign(new Error('Panel oturumu kapandı. Yeniden giriş yapın.'),{status:r.status});
      const result=await r.json();
      if(!r.ok){
        const reasons={onceki_konusmanin_sonucu_bilinmiyor:'Önceki isteğin sonucu bilinmiyor. Yeniden çalıştırmadım.',
          jeff_halen_dusunuyor:'Jeff önceki isteği değerlendiriyor. İsteği yeniden çalıştırmadım.',
          gercek_jeff_bagli_degil:'Gerçek Jeff bağlantısı açık değil.',gorusme_suresi_doldu:'Görüşme süresi doldu.',
          cok_sik:'Çok sık görüşme açıldı. Biraz bekleyin.'};
        throw Object.assign(new Error(reasons[result.error]||'Görüşme bağlantısı kurulamadı.'),{status:r.status});
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
      let r;
      try{r=await fetch('/api/voice/consult',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({...body,stream:true}),signal});}
      catch(e){
        // Lost headers do not prove the server never admitted the request.
        // Inspect only this owner's exact journal entry. Never resubmit it.
        if(signal?.aborted||e.name==='AbortError'||!body.session||!body.call_id)throw e;
        const result=await this.recoverConsultResult(body,signal);
        onPiece({authority:'real_jeff',answer:result.answer,completion_verified:false});return result;
      }
      if(!r.ok){
        const data=await r.json().catch(()=>({}));
        const reasons={onceki_konusmanin_sonucu_bilinmiyor:'Önceki isteğin sonucu bilinmiyor. Yeniden çalıştırmadım.',
          jeff_halen_dusunuyor:'Jeff önceki isteği değerlendiriyor. İsteği yeniden çalıştırmadım.'};
        throw new Error(reasons[data.error]||'Jeff yanıtı alınamadı.');
      }
      const reader=r.body.getReader(),decoder=new TextDecoder();let buffer='',result=null,accepted=false,received='';
      try{
        while(true){
          const {done,value}=await reader.read();buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});
          let end;
          while((end=buffer.indexOf('\n'))>=0){
            const line=buffer.slice(0,end);buffer=buffer.slice(end+1);if(!line.trim())continue;
            const event=JSON.parse(line);
            if(event.t==='accepted'){accepted=true;onAccepted?.(event);}
            if(event.t==='err')throw Object.assign(new Error(event.error==='ses_model_hakki_dolu'
              ? 'Jeff’in cevap bağlantılarındaki kullanım hakkı dolu.'
              : 'Jeff cevabı tamamlanamadı. Sonuç doğrulanmadı.'),{reason:event.error});
            if(event.t==='piece'){received+=event.answer||'';onPiece(event);}
            if(event.t==='end')result=event;
          }
          if(done)break;
        }
        if(buffer.trim()||!result)throw new Error('Jeff cevabı yarım kaldı. Sonuç doğrulanmadı.');
        return result;
      }catch(e){
        if(!accepted||signal?.aborted||e.name==='AbortError'||e.reason==='ses_model_hakki_dolu')throw e;
        const recovered=await this.recoverConsultResult(body,signal);
        const tail=recovered.answer.startsWith(received)?recovered.answer.slice(received.length):'Son doğrulanmış cevap: '+recovered.answer;
        if(tail)onPiece({authority:'real_jeff',answer:tail,completion_verified:false});
        return recovered;
      }finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
    }
    async recoverConsultResult(body,signal){
      // Only inspect the journal; never submit the question again after a lost stream.
      const deadline=performance.now()+90000;
      while(!signal?.aborted&&this.active&&performance.now()<deadline){
        let result;
        try{result=await this.post('result',{session:body.session,call_id:body.call_id},signal);}
        catch(e){if(signal?.aborted||(e.status&&e.status<500))throw e;}
        if(result){
        if(result.state==='ANSWERED'&&result.authority==='real_jeff'&&result.answer){
          this.stats.resultRecoveries=(this.stats.resultRecoveries||0)+1;
          return {t:'end',...result,cached:true,completion_verified:false};
        }
        if(result.state!=='RUNNING')throw new Error('İsteğin sonucu doğrulanamadı. Tekrar çalıştırmadım.');
        }
        await new Promise((resolve,reject)=>{
          const finish=()=>{signal?.removeEventListener('abort',abort);resolve();};
          const timer=setTimeout(finish,2000);
          const abort=()=>{clearTimeout(timer);signal?.removeEventListener('abort',abort);reject(new DOMException('Görüşme kapandı.','AbortError'));};
          signal?.addEventListener('abort',abort,{once:true});if(signal?.aborted)abort();
        });
      }
      if(signal?.aborted)throw new DOMException('Görüşme kapandı.','AbortError');
      throw new Error('Sonuç henüz alınamadı. Başlatılmış işi tekrar çalıştırmadım.');
    }
    fail(message){this.stop();this.notice(message);}
    stop(){
      if(this.inputText){this.commitInput();this.inputText='';}
      if(this.outputText){if(!this.canonicalOutput)this.remember('assistant','[Görüşme kapanırken kesilen yanıt] '+this.outputText);this.outputText='';}
      const session=this.session?.session;this.active=false;++this.generation;clearTimeout(this.expiry);
      clearTimeout(this.announcementTimer);this.announcement?.abort();this.resultAnnouncements=[];
      clearTimeout(this.replyWatch);this.clearHeldAudio();this.resumeHandle=null;
      this.reconnecting=false;
      for(const ac of this.pending.values())ac.abort();this.pending.clear();this.flushAudio();
      for(const ac of this.background.values())ac.abort();this.background.clear();this.completedCalls.clear();
      this.callResults.clear();this.answerCall=null;
      this.turnOutcomes.clear();
      clearTimeout(this.utteranceTimer);this.utterance=null;this.unboundCalls=[];this.providerBindings.clear();
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
