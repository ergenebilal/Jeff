const test=require('node:test'),assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const {JeffLiveCall}=require('./live-call.js');
function fixture(){return new JeffLiveCall({state:()=>{},transcript:()=>{},notice:()=>{},voice:()=> 'Charon',worklet:'fixture'});}

test('audio arriving before its Turkish greeting transcript is buffered then played once',()=>{
 const call=fixture();call.active=true;call.fastDialogue=new Set(['merhaba jeff']);let played=0;
 call.play=()=>played++;
 call.receive({serverContent:{modelTurn:{parts:[{inlineData:{data:'AAAA',mimeType:'audio/pcm;rate=24000'}}]},outputTranscription:{text:'Merhaba.'}}},0);
 assert.equal(played,0);
 call.receive({serverContent:{inputTranscription:{text:'Merhaba Jeff.'}}},0);
 assert.equal(played,1);assert.equal(call.outputText,'Merhaba.');assert.equal(call.heldAudio.length,0);
});
test('unverified buffered audio never leaks when a real tool answer arrives',async()=>{
 const call=fixture();call.active=true;call.session={session:'fixture'};call.ws={send:()=>{}};
 call.play=()=>assert.fail('ungrounded pre-tool audio');
 call.receive({serverContent:{modelTurn:{parts:[{inlineData:{data:'AAAA'}}]}}},0);
 call.postConsult=async()=>({authority:'real_jeff',answer:'Sonuç doğrulanmadı.'});
 await call.consult({id:'x',name:'consult_jeff',args:{text:'Tamamlandı mı?'}},0);
 assert.equal(call.heldAudio.length,0);assert.equal(call.audioAllowed,true);
});
test('unclear Turkish speech receives a narrow clarification without duplicating transcript',()=>{
 const call=fixture();call.active=true;call.singleBrain=true;let played=0;call.play=()=>played++;
 call.receive({serverContent:{modelTurn:{parts:[{inlineData:{data:'AAAA'}}]}}},0);
 const text='Son söylediğini anlayamadım, Türkçe tekrar eder misin?';
 call.receive({serverContent:{outputTranscription:{text}}},0);
 assert.equal(played,1);assert.equal(call.outputText,text);
});
test('local noise while Jeff is thinking does not cancel a durable request',async()=>{
 const call=fixture();call.active=true;call.durableRequests=true;call.session={session:'fixture'};
 let finish,sends=0;call.ws={send:()=>sends++};call.postConsult=()=>new Promise(r=>finish=r);
 const task=call.consult({id:'x',name:'consult_jeff',args:{text:'Bir fikrim var.'}},0);
 call.onInputActivity();assert.equal(call.pending.size,1);assert.equal(call.pending.get('x').signal.aborted,false);
 finish({authority:'real_jeff',answer:'Birlikte düşünelim.'});await task;assert.equal(sends,1);
});
test('confirmed interruption keeps the job and delivers its eventual result without old audio',async()=>{
 const call=fixture();call.active=true;call.durableRequests=true;call.session={session:'fixture'};
 let finish,sends=0,shown=[];call.ws={send:()=>sends++};call.transcript=(role,text)=>shown.push(text);
 call.postConsult=()=>new Promise(r=>finish=r);
 const task=call.consult({id:'x',name:'consult_jeff',args:{text:'Bir fikrim var.'}},0);
 const ac=call.pending.get('x');call.receive({toolCallCancellation:{ids:['x']}},0);
 assert.equal(ac.signal.aborted,false);assert.equal(call.pending.size,0);
 finish({authority:'real_jeff',answer:'Önce küçük bir deneme yap.'});await task;
 assert.equal(sends,0);assert.match(shown.join(' '),/küçük bir deneme/);assert.equal(call.background.size,0);
});
test('recovering idle audio connection uses new token and never replays microphone or tools',async()=>{
 const call=fixture();call.active=true;call.resumeHandle='private-handle';call.session={session:'original',expires_at:Date.now()/1000+1200};
 let oldClosed=0,renewed=0,opened=0;call.ws={close:()=>oldClosed++};call.post=async(action,body)=>{
  assert.equal(action,'renew');assert.equal(body.session,'original');renewed++;return {expires_at:Date.now()/1000+1200};};
 call.openSocket=async()=>opened++;await call.recoverConnection();
 assert.equal(oldClosed,1);assert.equal(renewed,1);assert.equal(opened,1);assert.equal(call.active,true);
 assert.equal(call.session.session,'original');clearTimeout(call.expiry);
});
test('a stale resumption token is discarded when provider declares session not resumable',()=>{
 const call=fixture();call.resumeHandle='old';call.receive({sessionResumptionUpdate:{resumable:false}},0);
 assert.equal(call.resumeHandle,null);
});
test('provider replay of a completed tool ID cannot execute the request twice',async()=>{
 const call=fixture();call.active=true;call.session={session:'fixture'};call.ws={send:()=>{}};let executions=0;
 call.postConsult=async()=>{executions++;return {authority:'real_jeff',answer:'Yanıt.'};};
 const request={id:'same',name:'consult_jeff',args:{text:'Fikrimi değerlendir.'}};
 await call.consult(request,0);call.lastCall='another';await call.consult(request,0);assert.equal(executions,1);
});
test('same pending question under a new provider ID does not call Jeff or announce failure twice',async()=>{
 const call=fixture();call.active=true;call.session={session:'fixture'};let finish,executions=0,sends=[];
 call.ws={send:data=>sends.push(JSON.parse(data))};call.postConsult=()=>{executions++;return new Promise(r=>finish=r);};
 const first=call.consult({id:'original',name:'consult_jeff',args:{text:'Karar yorgunluğunu açıkla.'}},0);
 await call.consult({id:'different',name:'consult_jeff',args:{text:'Karar yorgunluğunu açıkla.'}},0);
 assert.equal(executions,1);assert.equal(call.pending.size,1);
 assert.equal(sends[0].toolResponse.functionResponses[0].scheduling,'SILENT');
 finish({authority:'real_jeff',answer:'Seçim yaptıkça zihinsel yorgunluk oluşur.'});await first;
 assert.equal(sends.length,2);assert.equal(call.stats.duplicateRequestsSuppressed,1);
});

test('a completed detached answer is queued as exact speech without asking Jeff again',async()=>{
 const call=fixture();call.active=true;call.lastInputAt=-1000;let spoken;
 call.scheduleResultSpeech=()=>{};call.streamCanonicalSpeech=async text=>spoken=text;
 call.enqueueResultSpeech('Önceki isteğinin sonucu: Deneme hazır.',0);
 call.pending.set('busy',{});await call.drainResultSpeech();assert.equal(spoken,undefined);
 call.pending.clear();await call.drainResultSpeech();assert.equal(spoken,'Önceki isteğinin sonucu: Deneme hazır.');
 assert.equal(call.resultAnnouncements.length,0);assert.equal(call.announcement,null);
});
test('input activity immediately stops a result announcement without stopping its job',()=>{
 const call=fixture();call.active=true;call.durableRequests=true;const ac=call.announcement=new AbortController();
 let stops=0;call.sources.add({stop:()=>stops++});call.onInputActivity();
 assert.equal(ac.signal.aborted,true);assert.equal(stops,1);assert.equal(call.active,true);
});
test('muting during input leaves completed result delivery unblocked',()=>{
 global.WebSocket={OPEN:1};
 const call=fixture();call.active=true;call.inputActive=true;call.stream={getAudioTracks:()=>[{enabled:true}]};
 assert.equal(call.mute(),true);assert.equal(call.inputActive,false);
});
test('old call generation results are not spoken in a new conversation',async()=>{
 const call=fixture();call.active=true;call.generation=2;call.lastInputAt=-1000;call.scheduleResultSpeech=()=>{};
 call.streamCanonicalSpeech=()=>assert.fail('stale speech');call.enqueueResultSpeech('Eski sonuç.',1);
 await call.drainResultSpeech();assert.equal(call.resultAnnouncements.length,0);
});
test('canonical speech preserves odd network boundaries and never sends a new Jeff request',async()=>{
 const call=fixture();call.active=true;const ac=new AbortController();let sent=[],played=[],index=0,cancelled=0;
 const original=global.fetch;global.fetch=async(url,options)=>{
  assert.equal(url,'/api/tts/stream');sent.push(JSON.parse(options.body).text);
  const parts=[new Uint8Array([1]),new Uint8Array([2,3,4])];
  return {ok:true,headers:{get:()=> '24000'},body:{getReader:()=>({read:async()=>index<parts.length?{done:false,value:parts[index++]}:{done:true},cancel:async()=>cancelled++,releaseLock:()=>{}})}};
 };
 try{call.play=x=>played.push([...Buffer.from(x.data,'base64')]);await call.streamCanonicalSpeech('Sonuç aynen korunur.',ac.signal,0);
  assert.deepEqual(sent,['Sonuç aynen korunur.']);assert.deepEqual(played,[[1,2,3,4]]);assert.equal(cancelled,1);
 }finally{global.fetch=original;}
});
test('an interrupted speech response cannot play late chunks',async()=>{
 const call=fixture();call.active=true;const ac=new AbortController();const original=global.fetch;
 global.fetch=async()=>({ok:true,headers:{get:()=> '24000'},body:{getReader:()=>({read:async()=>{ac.abort();return {done:false,value:new Uint8Array([1,2])};},cancel:async()=>{},releaseLock:()=>{}})}});
 try{call.play=()=>assert.fail('late chunk');await call.streamCanonicalSpeech('Sonuç.',ac.signal,0);}finally{global.fetch=original;}
});
test('reconnecting aborts announcement before opening a fresh socket',async()=>{
 const call=fixture();call.active=true;call.resumeHandle='handle';call.session={session:'test'};
 const ac=call.announcement=new AbortController();call.ws={close:()=>{}};
 call.post=async()=>({expires_at:Date.now()/1000+1200});call.openSocket=async()=>assert.equal(ac.signal.aborted,true);
 await call.recoverConnection();clearTimeout(call.expiry);
});
test('incomplete final PCM is reported rather than treated as successful speech',async()=>{
 const call=fixture();call.active=true;const ac=new AbortController();const original=global.fetch;let n=0;
 global.fetch=async()=>({ok:true,headers:{get:()=> '24000'},body:{getReader:()=>({read:async()=>n++?{done:true}:{done:false,value:new Uint8Array([1])},cancel:async()=>{},releaseLock:()=>{}})}});
 try{await assert.rejects(call.streamCanonicalSpeech('Sonuç.',ac.signal,0),/incomplete_result_audio/);}finally{global.fetch=original;}
});

test('lost accepted response reads its journal and never submits the question twice',async()=>{
 const call=fixture();call.active=true;let requests=0,pieces=[],reads=0;const original=global.fetch;
 global.fetch=async(url)=>{
  assert.equal(url,'/api/voice/consult');requests++;
  return {ok:true,body:{getReader:()=>({read:async()=>{if(reads++)throw new TypeError('network');return {done:false,value:Buffer.from('{"t":"accepted"}\n{"t":"piece","answer":"İlk cümle. ","authority":"real_jeff"}\n')};},cancel:async()=>{},releaseLock:()=>{}})}};
 };
 call.post=async(action,body)=>{assert.equal(action,'result');assert.equal(body.call_id,'one');return {state:'ANSWERED',authority:'real_jeff',answer:'İlk cümle. Son cümle.'};};
 try{const answer=await call.postConsult({session:'s',call_id:'one'},new AbortController().signal,e=>pieces.push(e.answer));
  assert.equal(requests,1);assert.deepEqual(pieces,['İlk cümle. ','Son cümle.']);assert.equal(answer.completion_verified,false);
 }finally{global.fetch=original;}
});
test('an unknown journal outcome is reported and cannot cause a new execution',async()=>{
 const call=fixture();call.active=true;let reads=0;call.post=async action=>{assert.equal(action,'result');reads++;return {state:'OUTCOME_UNKNOWN',authority:'real_jeff'};};
 await assert.rejects(call.recoverConsultResult({session:'s',call_id:'one'},new AbortController().signal),/Tekrar çalıştırmadım/);
 assert.equal(reads,1);
});
test('closing a lost response cancels result recovery promptly',async()=>{
 const call=fixture();call.active=true;const ac=new AbortController();call.post=async()=>({state:'RUNNING'});
 const task=call.recoverConsultResult({session:'s',call_id:'one'},ac.signal);setTimeout(()=>ac.abort(),10);
 await assert.rejects(task,e=>e.name==='AbortError');
});
test('unaccepted network errors cannot query or replay a nonexistent job',async()=>{
 const call=fixture();call.active=true;const original=global.fetch;call.post=()=>assert.fail('not admitted');
 global.fetch=async()=>{throw new TypeError('network');};
 try{await assert.rejects(call.postConsult({},new AbortController().signal,()=>{}),/network/);}finally{global.fetch=original;}
});

test('owner work agenda has its own operation and one complete grounded response',async()=>{
 const call=fixture();call.active=true;let sent=[],body;
 call.session={session:'fixture'};call.ws={send:text=>sent.push(JSON.parse(text))};
 call.postConsult=async(request,signal,onPiece)=>{body=request;onPiece({authority:'real_jeff',answer:'Alpha: taslağı incele. '});return {authority:'real_jeff',answer:'Alpha: taslağı incele. Sonraki adım ses bağlamı.'};};
 await call.consult({id:'agenda',name:'read_work_agenda',args:{text:'Ne iş var?'}},call.generation);
 assert.equal(body.operation,'agenda');assert.equal(sent.length,1);
 assert.equal(sent[0].toolResponse.functionResponses[0].name,'read_work_agenda');
 assert.match(sent[0].toolResponse.functionResponses[0].response.answer,/Alpha.*Sonraki adım/);
 assert.equal(sent[0].toolResponse.functionResponses[0].willContinue,false);
});

test('saved radar summary is a bounded read and not an agent action',async()=>{
 const call=fixture();call.active=true;let sent=[],body;
 call.session={session:'fixture'};call.ws={send:text=>sent.push(JSON.parse(text))};
 call.postConsult=async(request,signal,onPiece)=>{body=request;onPiece({authority:'real_jeff',answer:'Son tarama kaydı tamamlandı. '});return {authority:'real_jeff',answer:'Son tarama kaydı tamamlandı. Kayıtlı haber: Alpha.'};};
 await call.consult({id:'radar',name:'read_radar_summary',args:{text:'Haber özeti'}},call.generation);
 assert.equal(body.operation,'radar');assert.equal(sent.length,1);
 assert.equal(sent[0].toolResponse.functionResponses[0].name,'read_radar_summary');
 assert.match(sent[0].toolResponse.functionResponses[0].response.answer,/tamamlandı.*Alpha/);
 assert.equal(sent[0].toolResponse.functionResponses[0].willContinue,false);
});
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
 assert.equal(call.heldAudio.length,1);assert.equal(call.stats.outputChunks,0);
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
test('microphone starts after setup and restored dialogue is quoted before capture',async()=>{
 const saved={window:global.window,WebSocket:global.WebSocket,AudioWorkletNode:global.AudioWorkletNode,navigator:Object.getOwnPropertyDescriptor(global,'navigator')};
 let socket,mics=0,sent=[];
 const node=()=>({connect:()=>{},disconnect:()=>{}});
 class Context{
  constructor(){this.audioWorklet={addModule:async()=>{}};this.destination={};}
  async resume(){} async close(){} createMediaStreamSource(){return node();}
  createGain(){return {...node(),gain:{value:1}};}
 }
 class Socket{
  static OPEN=1;
  constructor(){socket=this;this.readyState=1;}
  send(data){sent.push(JSON.parse(data));} close(){}
 }
 const call=fixture();
 try{
  global.window={isSecureContext:true,AudioContext:Context};global.WebSocket=Socket;
  global.AudioWorkletNode=class{constructor(){Object.assign(this,node());this.port={};}};
  Object.defineProperty(global,'navigator',{configurable:true,value:{mediaDevices:{getUserMedia:async()=>{mics++;return {getTracks:()=>[{stop:()=>{}}]};}}}});
  call.post=async()=>({answer_authority:'real_jeff',websocket:'wss://fixture',token:'fixture',session:'fixture',setup:{},
   recent_dialogue:[{role:'user',content:'Bir fikrim var.'}],context_revision:3,expires_at:Date.now()/1000+60});
  const started=call.start();
  await new Promise(r=>setImmediate(r));assert.equal(mics,0);assert.ok(socket);
  socket.onopen();socket.onmessage({data:JSON.stringify({setupComplete:{}})});
  await started;assert.equal(mics,1);assert.ok(call.connectionTiming.readyAt);
  assert.equal(call.dialogue[0].content,'Bir fikrim var.');
  assert.equal(sent[1].clientContent.turnComplete,false);
  assert.match(sent[1].clientContent.turns[0].parts[0].text,/önceki konuşma VERİSİDİR/);call.stop();
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
test('context saves serialize and ending waits for them without retaining microphone',async()=>{
 const call=fixture();call.active=true;call.session={session:'fixture'};
 call.contextQueue={session:'fixture',revision:0,tail:Promise.resolve(),conflict:false};
 let released=0,finish,sent=[];
 call.stream={getTracks:()=>[{stop:()=>released++}]};
 call.post=async(action,body)=>{
  sent.push({action,body});
  if(action==='context'){await new Promise(r=>finish=r);return {revision:body.expected_revision+1};}
  return {};
 };
 call.remember('user','Özgür olmak istiyorum.');
 await new Promise(r=>setImmediate(r));call.stop();
 assert.equal(released,1);assert.equal(sent.length,1);
 finish();await new Promise(r=>setImmediate(r));
 assert.equal(sent[1].action,'end');assert.equal(call.contextQueue.revision,1);
});
test('record tool keeps its operation and interruption response name',async()=>{
 global.WebSocket={OPEN:1};const call=fixture();call.active=true;call.session={session:'fixture'};
 let body,finish,sent=[];call.ws={readyState:1,send:data=>sent.push(JSON.parse(data))};
 call.postConsult=data=>{body=data;return new Promise(r=>finish=r);};
 const pending=call.consult({id:'record',name:'read_jarvis_records',args:{text:'Hangi işler bekliyor?'}},call.generation);
 assert.equal(body.operation,'records');assert.equal(body.text,'Hangi işler bekliyor?');
 call.onInputActivity();
 assert.equal(sent[0].toolResponse.functionResponses[0].name,'read_jarvis_records');
 finish({authority:'real_jeff',answer:'Geç yanıt'});await pending;assert.equal(sent.length,1);
});
test('bounded record figures are sent together even after progress was spoken',async()=>{
 const call=fixture();call.active=true;call.session={session:'fixture'};let finish,sent=[];
 call.ws={send:data=>sent.push(JSON.parse(data))};
 call.postConsult=(_,__,piece,accepted)=>{
  accepted({authority:'real_jeff',progress:'Kontrol ediyorum.'});
  return new Promise(resolve=>finish=()=>{
   piece({authority:'real_jeff',answer:'16 açık iş. '});piece({authority:'real_jeff',answer:'10 sonuç doğrulanmadı.'});
   resolve({authority:'real_jeff',answer:'16 açık iş. 10 sonuç doğrulanmadı.'});
  });
 };
 const pending=call.consult({id:'record',name:'read_jarvis_records',args:{text:'Hangi işler bekliyor?'}},call.generation);
 await new Promise(r=>setTimeout(r,550));assert.equal(sent.length,1);finish();await pending;
 assert.equal(sent.length,2);const response=sent[1].toolResponse.functionResponses[0];
 assert.equal(response.response.answer,'16 açık iş. 10 sonuç doğrulanmadı.');
 assert.equal(response.scheduling,'INTERRUPT');assert.equal(response.willContinue,false);
});
test('barge-in preserves the previous utterance without joining it to the next request',()=>{
 const call=fixture();call.active=true;call.inputOpen=true;call.inputText='Önceki soru.';call.outputText='Yarım yanıt.';
 call.sources.add({stop:()=>{}});call.onInputActivity();
 call.receive({serverContent:{inputTranscription:{text:'Dur, beni dinle.'}}},call.generation);
 assert.equal(call.inputText,'Dur, beni dinle.');
 assert.deepEqual(call.dialogue.map(m=>m.role),['user','assistant']);
 assert.equal(call.dialogue[0].content,'Önceki soru.');assert.match(call.dialogue[1].content,/Sözü kesilen/);
});
