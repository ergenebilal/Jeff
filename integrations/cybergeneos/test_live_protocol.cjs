const test=require('node:test'),assert=require('node:assert/strict');
const {JeffLiveCall}=require('./live-call.js');
function fixture(){
 const sent=[],notices=[];
 const call=new JeffLiveCall({state:()=>{},transcript:()=>{},notice:s=>notices.push(s),voice:()=> 'Charon',worklet:'fixture',routeUtterances:false});
 call.active=true;call.durableRequests=true;call.session={session:'fixture'};
 call.ws={send:s=>sent.push(JSON.parse(s)),close:()=>{}};
 return {call,sent,notices};
}

test('known capacity refusal is terminal without journal polling or a second submission',async()=>{
 const {call}=fixture(),original=global.fetch;let requests=0,reads=0,accepted=0;
 global.fetch=async()=>{requests++;return {ok:true,body:{getReader:()=>({
   read:async()=>reads++?{done:true}:{done:false,value:new TextEncoder().encode(
     '{"t":"accepted","authority":"real_jeff"}\n{"t":"err","error":"ses_model_hakki_dolu"}\n')},
   cancel:async()=>{},releaseLock:()=>{}
 })}};};
 call.recoverConsultResult=()=>assert.fail('capacity refusal must not wait on the journal');
 try{
  await assert.rejects(call.postConsult({session:'fixture',call_id:'capacity'},undefined,()=>{},()=>accepted++),
    error=>error.reason==='ses_model_hakki_dolu');
  assert.equal(requests,1);assert.equal(accepted,1);
 }finally{global.fetch=original;call.stop();}
});

test('capacity refusal tells the owner the actual cause and does not become a successful answer',async()=>{
 const {call}=fixture(),original=global.WebSocket;global.WebSocket={OPEN:1};
 call.routeUtterances=true;call.enqueueResultSpeech=()=>{};
 call.postConsult=async()=>{throw Object.assign(new Error('Kullanım hakkı dolu.'),{reason:'ses_model_hakki_dolu'});};
 try{
  call.receive({serverContent:{inputTranscription:{text:'Bir fikir düşünelim.'}}},0);
  await call.dispatchUtterance(call.utterance,0);
  const answer=call.dialogue.at(-1).content;
  assert.match(answer,/kullanım hakkı dolu/);assert.match(answer,/başlatmadım/);
  assert.doesNotMatch(answer,/sonucunu doğrulayamadım/);
  assert.equal([...call.turnOutcomes.values()].at(-1).completion_verified,false);
 }finally{call.stop();global.WebSocket=original;}
});

test('voice captures the selected opportunity when the human question starts',async()=>{
 const {call}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};
 let selected='20b52029e3604190',requests=[];call.opportunity=()=>selected;
 call.postConsult=async body=>{requests.push(body);return {authority:'real_jeff',answer:'Fixture only.'};};
 call.receive({serverContent:{inputTranscription:{text:'Bunu neden seçmiştin?'}}},0);
 const first=call.utterance;selected='0123456789abcdef';
 await call.dispatchUtterance(first,0);
 assert.equal(requests[0].opportunity_id,'20b52029e3604190');
 call.onInputActivity();call.inputActive=false;
 call.receive({serverContent:{inputTranscription:{text:'Bunu neden seçmiştin?'}}},0);
 await call.dispatchUtterance(call.utterance,0);
 assert.equal(requests.length,2);assert.equal(requests[1].opportunity_id,selected);call.stop();
});

test('canonical answer awaiting speech clears only its own recognition watchdog',()=>{
 const {call}=fixture();call.routeUtterances=true;call.scheduleResultSpeech=()=>{};
 const cleared=[],original=global.clearTimeout;
 global.clearTimeout=id=>cleared.push(id);
 try{
  call.replyWatch='current-question';call.utterance={result:{answer:'Gerçek cevap.'}};
  call.enqueueResultSpeech('Gerçek cevap.',0);assert.deepEqual(cleared,['current-question']);
  cleared.length=0;call.utterance={text:'Yeni soru',result:null};
  call.enqueueResultSpeech('Önceki isteğinin sonucu: Gerçek cevap.',0);assert.deepEqual(cleared,[]);
 }finally{global.clearTimeout=original;}
});
test('one admitted request sends one complete result, not progress or sentence completions',async()=>{
 const {call,sent}=fixture();let finish;
 call.postConsult=(_,__,piece,accepted)=>{
  accepted({authority:'real_jeff',progress:'Kontrol ediyorum.'});
  piece({authority:'real_jeff',answer:'İlk cümle. '});
  piece({authority:'real_jeff',answer:'İkinci cümle.'});
  return new Promise(resolve=>finish=resolve);
 };
 const task=call.consult({id:'one',name:'consult_jeff',args:{text:'Bir örnek açıkla.'}},0);
 assert.equal(sent.length,0);
 finish({authority:'real_jeff',answer:'İlk cümle. İkinci cümle.'});await task;
 assert.equal(sent.length,1);
 const response=sent[0].toolResponse.functionResponses[0];
 assert.deepEqual(Object.keys(response).sort(),['id','name','response']);
 assert.equal(response.response.scheduling,'SILENT');
 assert.equal(response.response.answer,'İlk cümle. İkinci cümle.');
});
test('six consecutive questions keep canonical answers, not the speech model paraphrase',async()=>{
 const {call,sent}=fixture();call.play=()=>{};call.enqueueResultSpeech=()=>{};
 for(let i=1;i<=6;i++){
  call.onInputActivity();call.inputActive=false;
  const text=`Soru ${i}?`,answer=`Gerçek cevap ${i}.`;
  call.receive({serverContent:{inputTranscription:{text}}},0);
  call.postConsult=async(_,__,piece)=>{piece({authority:'real_jeff',answer});return {authority:'real_jeff',answer};};
  await call.consult({id:`call-${i}`,name:'consult_jeff',args:{text}},0);
  call.receive({serverContent:{outputTranscription:{text:`Sesli ifade ${i}.`},turnComplete:true}},0);
  if(call.answerCall)call.answerCall.awaiting=false;
 }
 assert.equal(sent.length,6);assert.equal(call.pending.size,0);
 assert.deepEqual(call.dialogue.map(m=>m.content),Array.from({length:6},(_,i)=>[`Soru ${i+1}?`,`Gerçek cevap ${i+1}.`]).flat());
});
test('replayed completed provider call receives cached answer without another Jeff execution',async()=>{
 const {call,sent}=fixture();let executions=0;
 call.postConsult=async()=>{executions++;return {authority:'real_jeff',answer:'Kaydedilmiş cevap.'};};
 const request={id:'repeat',name:'consult_jeff',args:{text:'Bir örnek açıkla.'}};
 await call.consult(request,0);await call.consult(request,0);
 assert.equal(executions,1);assert.equal(sent.length,2);
 assert.equal(sent[1].toolResponse.functionResponses[0].response.answer,'Kaydedilmiş cevap.');
 assert.equal(sent[1].toolResponse.functionResponses[0].response.scheduling,'SILENT');
});
test('tool call preceding transcription still records the original question once',async()=>{
 const {call}=fixture();call.postConsult=async()=>({authority:'real_jeff',answer:'Gerçek cevap.'});
 await call.consult({id:'early',name:'consult_jeff',args:{text:'Asıl sorum.'}},0);
 call.receive({serverContent:{inputTranscription:{text:'Asıl sorum.'},outputTranscription:{text:'Gerçek cevap.'},turnComplete:true}},0);
 assert.deepEqual(call.dialogue,[{role:'user',content:'Asıl sorum.'},{role:'assistant',content:'Gerçek cevap.'}]);
});
test('a new provider input cannot inherit permission from the previous Jeff answer',async()=>{
 const {call}=fixture();call.postConsult=async()=>({authority:'real_jeff',answer:'Gerçek cevap.'});
 await call.consult({id:'first',name:'consult_jeff',args:{text:'İlk soru.'}},0);
 call.receive({serverContent:{outputTranscription:{text:'Gerçek cevap.'},turnComplete:true}},0);
 call.answerCall.awaiting=false;
 // Deliberately no local microphone activity: provider input is independently authoritative.
 call.receive({serverContent:{inputTranscription:{text:'Yeni soru.'}}},0);
 assert.equal(call.audioAllowed,false);assert.equal(call.consultedAnswer,false);
});
test('an unknown outcome cannot be executed again under a new provider ID in the same utterance',async()=>{
 global.WebSocket={OPEN:1};const {call,sent}=fixture();call.ws.readyState=1;let executions=0;
 call.postConsult=async()=>{executions++;throw new Error('unknown outcome');};
 await call.consult({id:'failed',name:'consult_jeff',args:{text:'Asıl soru.'}},0);
 await call.consult({id:'retry',name:'consult_jeff',args:{text:'Asıl soru.'}},0);
 assert.equal(executions,1);assert.equal(sent.length,2);
 assert.equal(sent[1].toolResponse.functionResponses[0].response.completion_verified,false);
 assert.equal(sent[1].toolResponse.functionResponses[0].response.scheduling,'SILENT');
});
test('only the exact canonical answer is queued for speech, native paraphrases and audio are discarded',async()=>{
 const {call}=fixture();let spoken=[],played=0,shown=[];
 call.enqueueResultSpeech=s=>spoken.push(s);call.play=()=>played++;call.transcript=(_,s)=>shown.push(s);
 call.postConsult=async()=>({authority:'real_jeff',answer:'Üç işin sonucu henüz doğrulanmadı.'});
 await call.consult({id:'truth',name:'consult_jeff',args:{text:'İşler tamamlandı mı?'}},0);
 call.receive({serverContent:{outputTranscription:{text:'Bütün işler tamamlandı.'},modelTurn:{parts:[{inlineData:{data:'AAAA'}}]},turnComplete:true}},0);
 assert.deepEqual(spoken,['Üç işin sonucu henüz doğrulanmadı.']);assert.equal(played,0);
 assert.deepEqual(shown,['Üç işin sonucu henüz doğrulanmadı.']);assert.equal(call.heldAudio.length,0);
});
test('an unknown answer cannot become cached factual speech or a rephrased new execution',async()=>{
 global.WebSocket={OPEN:1};const {call}=fixture();call.ws.readyState=1;
 let executions=0,played=0,spoken=[];call.play=()=>played++;call.enqueueResultSpeech=s=>spoken.push(s);
 call.postConsult=async()=>{executions++;throw new Error('unknown outcome');};
 await call.consult({id:'failed',name:'consult_jeff',args:{text:'Kaç kalem var?'}},0);
 call.receive({serverContent:{outputTranscription:{text:'Toplam 4 kalem var.'},modelTurn:{parts:[{inlineData:{data:'AAAA'}}]},turnComplete:true}},0);
 await call.consult({id:'rephrased',name:'consult_jeff',args:{text:'Kalem sayısını hesapla.'}},0);
 assert.equal(executions,1);assert.equal(played,0);assert.equal(spoken.length,1);
 assert.match(spoken[0],/doğrulayamadım/);assert.equal(call.dialogue.at(-1).content,spoken[0]);
});
test('a transcribed question reaches Jeff without any native model tool call',async()=>{
 const {call,sent}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let requests=[];
 call.postConsult=async body=>{requests.push(body);return {authority:'real_jeff',answer:'Gerçek cevap.'};};
 call.receive({serverContent:{inputTranscription:{text:'Özel bir konuyu konuşalım, bunu hafızaya kaydetme.'}}},0);
 await call.dispatchUtterance(call.utterance,0);
 assert.equal(requests.length,1);assert.equal(requests[0].text,'Özel bir konuyu konuşalım, bunu hafızaya kaydetme.');
 assert.equal(sent.length,0);assert.equal(call.dialogue.at(-1).content,'Gerçek cevap.');call.stop();
});
test('a native paraphrase or retry cannot change or duplicate the transcript request',async()=>{
 const {call,sent}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let requests=[];
 call.postConsult=async body=>{requests.push(body);return {authority:'real_jeff',answer:'Asıl isteğin cevabı.'};};
 call.bindProviderCall({id:'native-1',name:'consult_jeff',args:{text:'Bir iş başlat.'}});
 call.receive({serverContent:{inputTranscription:{text:'Sadece bir fikir konuşalım. İş başlatma.'}}},0);
 const utterance=call.utterance;await call.dispatchUtterance(utterance,0);
 call.bindProviderCall({id:'native-2',name:'consult_jeff',args:{text:'İşi başlat ve tekrar dene.'}});
 assert.equal(requests.length,1);assert.equal(requests[0].text,'Sadece bir fikir konuşalım. İş başlatma.');
 assert.equal(sent.length,2);assert.ok(sent.every(s=>s.toolResponse.functionResponses[0].response.answer==='Asıl isteğin cevabı.'));call.stop();
});
test('late transcription after dispatch does not open a second utterance',async()=>{
 const {call}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let requests=0,finish;
 call.postConsult=()=>{requests++;return new Promise(r=>finish=r);};
 call.receive({serverContent:{inputTranscription:{text:'Bir soru.'}}},0);
 const utterance=call.utterance,task=call.dispatchUtterance(utterance,0);await new Promise(r=>setImmediate(r));
 call.receive({serverContent:{inputTranscription:{text:'Bir soru.'}}},0);
 assert.equal(call.utterance,utterance);assert.equal(requests,1);
 finish({authority:'real_jeff',answer:'Gerçek cevap.'});await task;call.stop();
});
test('a native turn boundary cannot truncate a partly transcribed Turkish request',async()=>{
 const {call}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let text;
 call.postConsult=async body=>{text=body.text;return {authority:'real_jeff',answer:'Cevap.'};};
 call.receive({serverContent:{inputTranscription:{text:'Bunu hafızaya '},turnComplete:true}},0);
 call.receive({serverContent:{inputTranscription:{text:'kaydetme. Sadece konuşalım.'}}},0);
 await call.dispatchUtterance(call.utterance,0);
 assert.equal(text,'Bunu hafızaya kaydetme. Sadece konuşalım.');call.stop();
});
test('a follow-up spoken while Jeff is thinking waits once and includes the preceding answer',async()=>{
 const {call}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};
 let requests=[],finish;
 call.postConsult=body=>{requests.push(body);return requests.length===1?new Promise(r=>finish=r):Promise.resolve({authority:'real_jeff',answer:'İkinci cevap.'});};
 call.receive({serverContent:{inputTranscription:{text:'İlk soru.'}}},0);
 const first=call.dispatchUtterance(call.utterance,0);await new Promise(r=>setImmediate(r));
 call.onInputActivity();call.inputActive=false;
 call.receive({serverContent:{inputTranscription:{text:'Takip sorusu.'}}},0);
 const second=call.dispatchUtterance(call.utterance,0);await new Promise(r=>setImmediate(r));
 assert.equal(requests.length,1);finish({authority:'real_jeff',answer:'İlk gerçek cevap.'});await first;await second;
 assert.equal(requests.length,2);
 assert.deepEqual(requests[1].dialogue,[{role:'user',content:'İlk soru.'},{role:'assistant',content:'İlk gerçek cevap.'}]);call.stop();
});
test('a failed question does not prevent the next human utterance reaching Jeff',async()=>{
 global.WebSocket={OPEN:1};const {call}=fixture();call.ws.readyState=1;call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let executions=0;
 call.postConsult=async()=>{if(++executions===1)throw new Error('unknown outcome');return {authority:'real_jeff',answer:'İkinci gerçek cevap.'};};
 for(const text of ['İlk soru.','İkinci soru.']){
  call.onInputActivity();call.inputActive=false;
  call.receive({serverContent:{inputTranscription:{text}}},0);await call.dispatchUtterance(call.utterance,0);
 }
 assert.equal(executions,2);assert.equal(call.dialogue.at(-1).content,'İkinci gerçek cevap.');call.stop();
});
test('ending a call prevents a queued question from being submitted later',async()=>{
 const {call}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};let executions=0,release;
 call.brainQueue=new Promise(r=>release=r);call.postConsult=async()=>{executions++;return {authority:'real_jeff',answer:'Cevap.'};};
 call.receive({serverContent:{inputTranscription:{text:'Kuyrukta bekleyen soru.'}}},0);
 const task=call.dispatchUtterance(call.utterance,0);call.stop();release();await task;
 assert.equal(executions,0);
});
test('cancelled or old-socket tool bindings cannot send a result into a renewed socket',async()=>{
 const {call,sent}=fixture();call.routeUtterances=true;call.enqueueResultSpeech=()=>{};
 call.postConsult=async()=>({authority:'real_jeff',answer:'Gerçek cevap.'});
 call.receive({serverContent:{inputTranscription:{text:'Bir soru.'}}},0);
 call.bindProviderCall({id:'old',name:'consult_jeff',args:{text:'Bir soru.'}});
 call.bindProviderCall({id:'cancelled',name:'consult_jeff',args:{text:'Bir soru.'}});
 call.receive({toolCallCancellation:{ids:['cancelled']}},0);call.socketEpoch++;
 await call.dispatchUtterance(call.utterance,0);assert.equal(sent.length,0);call.stop();
});
