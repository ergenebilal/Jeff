const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const {JeffLiveCall}=require('./live-call.js');
function fixture(){return new JeffLiveCall({state:()=>{},transcript:()=>{},notice:()=>{},voice:()=> 'Charon',worklet:'fixture'});}
test('interruption stops output but leaves microphone running',()=>{
 const call=fixture();call.active=true;let stopped=0,trackStops=0,aborted=0;
 call.sources.add({stop:()=>stopped++});call.stream={getTracks:()=>[{stop:()=>trackStops++}]};
 call.pending.set('call',{abort:()=>aborted++});call.audioAllowed=true;
 call.receive({serverContent:{interrupted:true}},call.generation);
 assert.equal(stopped,1);assert.equal(trackStops,0);assert.equal(aborted,1);assert.equal(call.active,true);assert.equal(call.audioAllowed,false);
});
test('voice model cannot play unconsulted audio',()=>{
 const call=fixture();call.active=true;call.audioAllowed=false;call.play=()=>assert.fail('must not play');
 call.receive({serverContent:{modelTurn:{parts:[{inlineData:{data:'AAAA',mimeType:'audio/pcm;rate=24000'}}]}}},call.generation);
 assert.equal(call.stats.unconsultedAudioDropped,1);
});
test('cancelled consultation cannot send late result',async()=>{
 const call=fixture();call.active=true;let done,sends=0;
 call.session={session:'fixture'};call.ws={send:()=>sends++};call.postConsult=()=>new Promise(r=>done=r);
 const task=call.consult({id:'fixture',name:'consult_jeff',args:{text:'Durum?'}},call.generation);
 call.receive({toolCallCancellation:{ids:['fixture']}},call.generation);
 done({authority:'real_jeff',answer:'Yanıt'});await task;assert.equal(sends,0);assert.equal(call.audioAllowed,false);
});
test('tool boundary is not final voice completion',()=>{
 const call=fixture();call.active=true;call.pending.set('fixture',{});call.audioAllowed=false;
 call.receive({serverContent:{turnComplete:true}},call.generation);assert.equal(call.pending.size,1);
});
test('end call releases microphone and queued sound',()=>{
 const call=fixture();call.active=true;let tracks=0,closed=0,sounds=0;
 call.stream={getTracks:()=>[{stop:()=>tracks++}]};call.ws={close:()=>closed++};call.sources.add({stop:()=>sounds++});
 call.stop();assert.equal(tracks,1);assert.equal(closed,1);assert.equal(sounds,1);assert.equal(call.active,false);
});
test('real capture rates produce 20ms frames at 16kHz',()=>{
 for(const rate of [44100,48000]){
  const frames=[];let Processor;
  const context={AudioWorkletProcessor:class{constructor(){this.port={postMessage:b=>{if(b instanceof ArrayBuffer)frames.push(b.byteLength);}}}},
    sampleRate:rate,Int16Array,ArrayBuffer,registerProcessor:(_,p)=>Processor=p};
  vm.runInNewContext(fs.readFileSync(__dirname+'/mic-capture.js','utf8'),context);
  const p=new Processor();for(let pos=0;pos<rate;pos+=128)p.process([[new Float32Array(Math.min(128,rate-pos)).fill(.1)]]);
  assert.equal(frames.length,50);assert.ok(frames.every(n=>n===640));
 }
});
test('local speech start cancels thinking without stopping microphone or replaying',async()=>{
 global.WebSocket={OPEN:1};const call=fixture();call.active=true;let done,sends=[];
 call.session={session:'fixture'};call.ws={readyState:1,send:text=>sends.push(JSON.parse(text))};
 call.postConsult=()=>new Promise(r=>done=r);
 const task=call.consult({id:'waiting',name:'consult_jeff',args:{text:'Durum?'}},call.generation);
 call.onInputActivity();done({authority:'real_jeff',answer:'Geç kalan cevap'});await task;
 assert.equal(call.active,true);assert.equal(call.pending.size,0);assert.equal(call.audioAllowed,false);
 assert.equal(call.stats.localInterruptions,1);assert.equal(sends.length,1);
 assert.equal(sends[0].toolResponse.functionResponses[0].response.cancelled,true);
});
test('actual Jeff first sentence is sent before the answer finishes',async()=>{
 const call=fixture();call.active=true;let done,sends=[];
 call.session={session:'fixture'};call.ws={send:text=>sends.push(JSON.parse(text))};
 call.postConsult=(_,__,onPiece)=>{onPiece({authority:'real_jeff',answer:'Kanıt yok. '});return new Promise(r=>done=r);};
 const task=call.consult({id:'streaming',name:'consult_jeff',args:{text:'Durum?'}},call.generation);
 assert.equal(sends.length,1);assert.equal(sends[0].toolResponse.functionResponses[0].willContinue,true);
 assert.equal(call.pending.size,1);assert.equal(call.audioAllowed,true);
 done({authority:'real_jeff',answer:'Kanıt yok. İş tamamlanmadı.'});await task;
 assert.equal(sends.length,2);assert.equal(sends[1].toolResponse.functionResponses[0].scheduling,'SILENT');
 assert.equal(sends[1].toolResponse.functionResponses[0].willContinue,false);
});
test('native partial turn boundary retains permission for remaining actual Jeff pieces',()=>{
 const call=fixture();call.active=true;call.audioAllowed=true;call.outputText='İlk cümle.';call.pending.set('streaming',{});
 call.receive({serverContent:{turnComplete:true}},call.generation);
 assert.equal(call.audioAllowed,true);assert.equal(call.pending.size,1);
});
test('only exact approved brief dialogue can speak without a Jeff consultation',()=>{
 const call=fixture();call.active=true;call.fastDialogue=new Set(['merhaba jeff']);call.play=()=>{};
 call.receive({serverContent:{inputTranscription:{text:'Merhaba Jeff.'}}},call.generation);
 assert.equal(call.audioAllowed,true);
 call.inputOpen=false;
 call.receive({serverContent:{inputTranscription:{text:'Görev tamamlandı mı?'}}},call.generation);
 assert.equal(call.audioAllowed,false);
});
test('greeting followed by an action loses permission before tool result',()=>{
 const call=fixture();call.active=true;call.fastDialogue=new Set(['merhaba']);
 call.receive({serverContent:{inputTranscription:{text:'Merhaba'}}},call.generation);
 assert.equal(call.audioAllowed,true);
 call.receive({serverContent:{inputTranscription:{text:' görevi tamamla'}}},call.generation);
 assert.equal(call.audioAllowed,false);
});
test('microphone capture starts only after the voice connection accepts setup',async()=>{
 const saved={window:global.window,WebSocket:global.WebSocket,AudioWorkletNode:global.AudioWorkletNode,navigator:Object.getOwnPropertyDescriptor(global,'navigator')};
 let socket,mics=0;
 const node=()=>({connect:()=>{},disconnect:()=>{}});
 class Context{
  constructor(){this.audioWorklet={addModule:async()=>{}};this.destination={};}
  async resume(){} async close(){} createMediaStreamSource(){return node();}
  createGain(){return {...node(),gain:{value:1}};}
 }
 class Socket{
  static OPEN=1;
  constructor(){socket=this;this.readyState=1;}
  send(){} close(){}
 }
 const call=fixture();
 try{
  global.window={isSecureContext:true,AudioContext:Context};global.WebSocket=Socket;
  global.AudioWorkletNode=class{constructor(){Object.assign(this,node());this.port={};}};
  Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>{mics++;return {getTracks:()=>[{stop:()=>{}}]};}}}});
  call.post=async()=>({answer_authority:'real_jeff',websocket:'wss://fixture',token:'fixture',session:'fixture',setup:{},expires_at:Date.now()/1000+60});
  const started=call.start();
  await new Promise(r=>setImmediate(r));assert.equal(mics,0);assert.ok(socket);
  socket.onopen();socket.onmessage({data:JSON.stringify({setupComplete:{}})});
  await started;assert.equal(mics,1);assert.ok(call.connectionTiming.readyAt);call.stop();
 }finally{
  call.stop();global.window=saved.window;global.WebSocket=saved.WebSocket;global.AudioWorkletNode=saved.AudioWorkletNode;
  if(saved.navigator)Object.defineProperty(global,'navigator',saved.navigator);else delete global.navigator;
 }
});
test('ordinary conversation speaks directly but current records need Jeff',()=>{
 const call=fixture();call.active=true;call.nativeConversation=true;call.proofRequired=/onay|pablo|durum|görev|hatır|bugün/i;
 call.receive({serverContent:{inputTranscription:{text:'Neden insanlar kararsız kalır?'}}},call.generation);
 assert.equal(call.audioAllowed,true);assert.equal(call.voiceTurn.kind,'native_conversation');
 call.inputOpen=false;call.receive({serverContent:{inputTranscription:{text:'Bugün ne var?'}}},call.generation);
 assert.equal(call.audioAllowed,false);
});
test('slow admitted consultation speaks progress without claiming completion',async()=>{
 const call=fixture();call.active=true;let done,piece,sends=[];
 call.session={session:'fixture'};call.ws={send:text=>sends.push(JSON.parse(text))};
 call.postConsult=(_,__,onPiece,onAccepted)=>{piece=onPiece;onAccepted({authority:'real_jeff',progress:'Kontrol ediyorum.'});return new Promise(r=>done=r);};
 const task=call.consult({id:'slow',name:'consult_jeff',args:{text:'Durum?'}},call.generation);
 await new Promise(r=>setTimeout(r,550));
 assert.equal(sends.length,1);assert.equal(sends[0].toolResponse.functionResponses[0].response.completion_verified,false);
 assert.equal(call.timings[0].firstPieceAt,null);assert.ok(call.timings[0].progressSentAt);
 piece({authority:'real_jeff',answer:'Sonuç doğrulanmadı.'});done({authority:'real_jeff',answer:'Sonuç doğrulanmadı.'});await task;
 assert.equal(sends.length,3);assert.equal(sends[1].toolResponse.functionResponses[0].response.answer,'Sonuç doğrulanmadı.');
});
test('recent dialogue stays bounded and never supplies a system role',()=>{
 const call=fixture();for(let i=0;i<30;i++)call.remember('user','x'.repeat(1500));
 assert.ok(call.dialogue.length<=12);assert.ok(call.dialogue.reduce((n,m)=>n+m.content.length,0)<=6000);
 assert.ok(call.dialogue.every(m=>m.role==='user'&&m.content.length<=1200));
});
test('barge-in preserves the previous utterance without joining it to the next request',()=>{
 const call=fixture();call.active=true;call.inputOpen=true;call.inputText='Önceki soru.';call.outputText='Yarım yanıt.';
 call.sources.add({stop:()=>{}});call.onInputActivity();
 call.receive({serverContent:{inputTranscription:{text:'Dur, beni dinle.'}}},call.generation);
 assert.equal(call.inputText,'Dur, beni dinle.');
 assert.deepEqual(call.dialogue.map(m=>m.role),['user','assistant']);
 assert.equal(call.dialogue[0].content,'Önceki soru.');assert.match(call.dialogue[1].content,/Sözü kesilen/);
});
