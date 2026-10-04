/* One continuous, interruptible call. No recognition restart or per-turn send button. */
(function(root){
  class JeffLiveCall {
    constructor({state,transcript,notice,voice,worklet}){
      Object.assign(this,{state,transcript,notice,voice,worklet});
      this.active=false; this.generation=0; this.sources=new Set(); this.pending=new Map();
      this.stats={inputFrames:0,outputChunks:0,interruptions:0,localInterruptions:0,unconsultedAudioDropped:0};
      this.timings=[];this.speechEndedAt=null;this.voiceTurn=null;
    }
    async start(){
      if(this.active)return;
      if(!window.isSecureContext || !navigator.mediaDevices?.getUserMedia)
        throw new Error('Mikrofon için güvenli panel adresini açın.');
      this.active=true; const generation=++this.generation;
      const current=()=>this.active && this.generation===generation;
      this.state('connecting','Görüşme bağlanıyor');
      this.ctx=new (window.AudioContext||window.webkitAudioContext)();
      await this.ctx.resume(); // Executed from the owner's click, including on mobile.
      try{
        const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false});
        if(!current()){stream.getTracks().forEach(t=>t.stop());return;}
        this.stream=stream;this.muted=false;
        this.session=await this.post('session',{voice:this.voice()});
        if(!current())return;
        const session=this.session;
        if(session.answer_authority!=='real_jeff')throw new Error('Gerçek Jeff bağlantısı doğrulanamadı.');
        const ws=this.ws=new WebSocket(session.websocket+'?access_token='+encodeURIComponent(session.token));
        delete session.token; // Only the active connection needs the short-lived credential.
        this.audioAllowed=false;this.next=0;this.inputText='';this.outputText='';
        this.inputOpen=false;this.lastCall=null;
        let received=Promise.resolve();
        await new Promise((resolve,reject)=>{
          const timeout=setTimeout(()=>reject(new Error('Ses bağlantısı zamanında açılamadı.')),15000);
          ws.onopen=()=>{if(current())ws.send(JSON.stringify({setup:session.setup}));};
          ws.onerror=()=>{clearTimeout(timeout);reject(new Error('Ses bağlantısı kurulamadı.'));};
          ws.onclose=()=>{
            clearTimeout(timeout);
            if(current()){reject(new Error('Ses bağlantısı kapandı.'));this.fail('Görüşme bağlantısı koptu. Yarım kalan istek yeniden gönderilmedi.');}
          };
          ws.onmessage=e=>{
            // Blob decoding must preserve provider message order.
            received=received.then(async()=>{
              if(!current())return;
              const event=JSON.parse(typeof e.data==='string'?e.data:await e.data.text());
              if(event.setupComplete){clearTimeout(timeout);resolve();return;}
              this.receive(event,generation);
            }).catch(()=>{if(current())this.fail('Ses bağlantısında hata oldu. Görüşme kapatıldı.');});
          };
        });
        if(!current())return;
        await this.ctx.audioWorklet.addModule(this.worklet);
        if(!current())return;
        const node=this.capture=new AudioWorkletNode(this.ctx,'jeff-microphone');
        this.input=this.ctx.createMediaStreamSource(stream);
        const silent=this.silent=this.ctx.createGain();silent.gain.value=0;
        this.input.connect(node);node.connect(silent);silent.connect(this.ctx.destination);
        node.port.onmessage=e=>{
          if(!current()||this.muted||ws.readyState!==WebSocket.OPEN)return;
          if(e.data?.activity==='start'){this.onInputActivity();return;}
          if(e.data?.activity==='end'){this.speechEndedAt=performance.now();return;}
          if(ws.bufferedAmount>64000){this.fail('Ses bağlantısı yetişemedi. Görüşme kapatıldı.');return;}
          const bytes=new Uint8Array(e.data);let binary='';
          for(let i=0;i<bytes.length;i++)binary+=String.fromCharCode(bytes[i]);
          ws.send(JSON.stringify({realtimeInput:{audio:{data:btoa(binary),mimeType:'audio/pcm;rate=16000'}}}));
          this.stats.inputFrames++;
        };
        this.state('listening','Dinliyorum');
        this.expiry=setTimeout(()=>this.fail('Görüşme süresi doldu. Yeni görüşme açabilirsiniz.'),Math.max(0,session.expires_at*1000-Date.now()));
      }catch(e){if(current()){this.stop();throw e;}}
    }
    receive(event,generation){
      if(event.error){this.fail('Canlı ses hizmetine ulaşılamadı.');return;}
      if(event.goAway){
        // No blind audio or tool replay. A fresh call requires the owner to start it.
        this.notice('Ses bağlantısının süresi dolmak üzere; kapanırsa yeni görüşme açabilirsiniz.');
      }
      for(const id of event.toolCallCancellation?.ids||[]){
        this.pending.get(id)?.abort();this.pending.delete(id);this.audioAllowed=false;
      }
      const content=event.serverContent||{};
      if(content.interrupted){
        this.stats.interruptions++;this.flushAudio();this.audioAllowed=false;
        for(const ac of this.pending.values())ac.abort();this.pending.clear();
        this.outputText='';this.state('listening','Dinliyorum');
      }
      const heard=content.inputTranscription?.text;
      if(heard){
        // Input transcription has no guaranteed ordering relative to tool replies.
        if(!this.inputOpen){this.inputText='';this.inputOpen=true;}
        this.inputText+=heard;this.transcript('user',this.inputText,false);
      }
      for(const call of event.toolCall?.functionCalls||[])this.consult(call,generation);
      const spoken=content.outputTranscription?.text;
      if(spoken&&this.audioAllowed){this.outputText+=spoken;this.transcript('jeff',this.outputText,false);}
      for(const part of content.modelTurn?.parts||[]){
        if(!part.inlineData?.data)continue;
        if(!this.audioAllowed){this.stats.unconsultedAudioDropped++;continue;}
        this.play(part.inlineData);
      }
      if(content.turnComplete){
        // Tool-request boundaries also emit turnComplete; they are not answer completion.
        if(!this.pending.size && this.outputText){
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
      this.audioAllowed=false;
      if(!this.pending.size&&!this.sources.size)return;
      this.stats.interruptions++;this.stats.localInterruptions++;this.flushAudio();this.audioAllowed=false;
      const cancelled=[];
      for(const [id,ac] of this.pending){
        ac.abort();cancelled.push({id,name:'consult_jeff',willContinue:false,scheduling:'SILENT',response:{cancelled:true,
          answer:'Kullanıcı araya girdi. Bu cevabı seslendirme; yeni isteği dinle.'}});
      }
      this.pending.clear();this.outputText='';
      if(cancelled.length&&this.ws?.readyState===WebSocket.OPEN)
        this.ws.send(JSON.stringify({toolResponse:{functionResponses:cancelled}}));
      this.state('listening','Dinliyorum');
    }
    async consult(call,generation){
      if(call.name!=='consult_jeff'||typeof call.args?.text!=='string'||!call.id){
        this.fail('Sesli istek doğrulanamadı.');return;
      }
      if(this.lastCall===call.id || this.pending.has(call.id))return;
      this.lastCall=call.id;this.audioAllowed=false;this.outputText='';
      const timing={consultStartedAt:performance.now(),speechEndedAt:this.speechEndedAt,
        firstPieceAt:null,firstAudioAt:null,answerEndedAt:null};
      this.timings.push(timing);this.voiceTurn=timing;
      if(this.inputText){this.transcript('user',this.inputText,true);this.inputText='';}
      const ac=new AbortController();this.pending.set(call.id,ac);
      this.state('thinking','Jeff düşünüyor · sizi dinliyorum');
      try{
        let streamed=false;
        const result=await this.postConsult({session:this.session.session,call_id:call.id,text:call.args.text},ac.signal,event=>{
          if(!this.active||generation!==this.generation||ac.signal.aborted)return;
          if(event.authority!=='real_jeff'||!event.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
          if(timing.firstPieceAt===null)timing.firstPieceAt=performance.now();
          this.audioAllowed=true;
          this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,
            response:{answer:event.answer},willContinue:true,scheduling:streamed?'WHEN_IDLE':'INTERRUPT'}]}}));
          streamed=true;
        });
        if(!this.active||generation!==this.generation||ac.signal.aborted)return;
        if(result.authority!=='real_jeff'||!result.answer)throw new Error('Gerçek Jeff yanıtı alınamadı.');
        timing.answerEndedAt=performance.now();this.audioAllowed=true;this.inputOpen=false;
        this.ws.send(JSON.stringify({toolResponse:{functionResponses:[{id:call.id,name:call.name,
          response:streamed?{}:{answer:result.answer},willContinue:false,scheduling:streamed?'SILENT':'INTERRUPT'}]}}));
      }catch(e){
        if(e.name!=='AbortError'&&this.active&&generation===this.generation)
          this.fail(e.message||'Jeff yanıtı alınamadı.');
      }finally{if(this.pending.get(call.id)===ac)this.pending.delete(call.id);}
    }
    play(inline){
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
      const r=await fetch('/api/voice/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal});
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
    }
    async postConsult(body,signal,onPiece){
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
      const session=this.session?.session;this.active=false;++this.generation;clearTimeout(this.expiry);
      for(const ac of this.pending.values())ac.abort();this.pending.clear();this.flushAudio();
      if(this.ws){this.ws.onclose=this.ws.onmessage=this.ws.onerror=null;this.ws.close();this.ws=null;}
      this.stream?.getTracks().forEach(t=>t.stop());this.stream=null;
      this.capture?.disconnect();this.input?.disconnect();this.silent?.disconnect();
      this.ctx?.close().catch(()=>{});this.ctx=null;this.session=null;
      if(session)this.post('end',{session}).catch(()=>{});
      this.state('idle','Hazır');
    }
  }
  root.JeffLiveCall=JeffLiveCall;
  if(typeof module==='object')module.exports={JeffLiveCall};
})(typeof window==='object'?window:globalThis);
