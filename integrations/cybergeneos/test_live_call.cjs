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
