"""Exact, bounded replacement of the previous push-to-talk controls."""
MIC = r'''/* Continuous live call. */
const mic = $('#mic');
let lastReply = '';
const muteButton=document.createElement('button');
muteButton.type='button';muteButton.className='mic';muteButton.hidden=true;
muteButton.style.display='none';
muteButton.id='mic-mute';muteButton.setAttribute('aria-label','Mikrofonu kapat');
muteButton.innerHTML='<i class="ph ph-microphone-slash" aria-hidden="true"></i>';
mic.after(muteButton);
let liveBubble={user:null,jeff:null};
const liveCall=new JeffLiveCall({
  voice:()=>voiceName,worklet:new URL('mic-capture.js',location.href).href,
  state:(state,label)=>{
    setJeff(state==='connecting'?'thinking':state,label);
    const on=liveCall.active;mic.setAttribute('aria-pressed',String(on));
    mic.setAttribute('aria-label',on?'Görüşmeyi bitir':'Canlı görüşmeyi başlat');
    mic.innerHTML=`<i class="ph ${on?'ph-phone-disconnect':'ph-phone-call'}" aria-hidden="true"></i>`;
    muteButton.hidden=!on;
    muteButton.style.display=on?'grid':'none';
  },notice:toast,
  transcript:(who,text,final)=>{
    if(!liveBubble[who])liveBubble[who]=msg(who==='user'?'u':'j','<span class="t"></span>',who==='jeff'?jeffMeta():'Sesli');
    liveBubble[who].querySelector('.t').textContent=text;$('#thread').scrollTop=1e6;
    if(final)liveBubble[who]=null;
  }
});
function abortListening(){if(liveCall.active)liveCall.stop();}
function micHint(){
  const h=$('#mic-hint');h.hidden=window.isSecureContext&&!!navigator.mediaDevices?.getUserMedia;
  h.textContent=h.hidden?'':'Canlı görüşme için panelin güvenli https adresini açın. Yazarak konuşabilirsiniz.';
  mic.setAttribute('aria-label','Canlı görüşmeyi başlat');
  mic.innerHTML='<i class="ph ph-phone-call" aria-hidden="true"></i>';
}
mic.addEventListener('click',async()=>{
  if(liveCall.active){liveCall.stop();return;}
  stopAudio();askSeq++;liveBubble={user:null,jeff:null};
  try{await liveCall.start();}catch(e){toast(e.name==='NotAllowedError'?'Görüşme için tarayıcıda mikrofon izni verin.':e.message);}
});
muteButton.addEventListener('click',()=>{
  const muted=liveCall.mute();muteButton.setAttribute('aria-pressed',String(muted));
  muteButton.setAttribute('aria-label',muted?'Mikrofonu aç':'Mikrofonu kapat');
});
window.addEventListener('pagehide',()=>liveCall.stop());
'''


def patch_front(source):
    if source.count('function stopAudio(){')!=1:
        raise ValueError('Panel audio stop anchor changed')
    source=source.replace('function stopAudio(){',"function stopAudio(){\n  if ('speechSynthesis' in window) speechSynthesis.cancel();")
    start=source.index('/* Microphone. What you say goes straight to Jeff:')
    end=source.index("$('#voice-out').addEventListener",start)
    return source[:start]+MIC+source[end:]


def patch_html(source):
    marker='<script src="app.js"></script>'
    if source.count(marker)!=1:
        raise ValueError('Panel script anchor changed')
    return source.replace(marker,'<script src="live-call.js"></script>\n'+marker)
