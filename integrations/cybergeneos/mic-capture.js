/* Resample the actual capture rate to 16 kHz; transfer 20 ms PCM frames. */
class JeffMicrophone extends AudioWorkletProcessor {
  constructor(){super();this.phase=0;this.total=0;this.previous=0;this.frame=new Int16Array(320);this.used=0;this.speechFrames=0;this.silentFrames=0;this.speaking=false;}
  process(inputs){
    const input=inputs[0]?.[0];if(!input)return true;
    const step=sampleRate/16000;
    for(let i=0;i<input.length;i++){
      const current=input[i],at=this.total++;
      while(this.phase<=at){
        const mix=Math.max(0,Math.min(1,this.phase-(at-1)));
        const sample=Math.max(-1,Math.min(1,this.previous+(current-this.previous)*mix));
        this.frame[this.used++]=sample<0?Math.round(sample*32768):Math.round(sample*32767);
        this.phase+=step;
        if(this.used===320){
          let energy=0;for(const n of this.frame)energy+=(n/32768)**2;
          const voiced=Math.sqrt(energy/320)>.014;
          this.speechFrames=voiced?this.speechFrames+1:0;
          this.silentFrames=voiced?0:this.silentFrames+1;
          // Local interruption only. Provider detection still decides utterance boundaries.
          if(!this.speaking&&this.speechFrames>=4){this.speaking=true;this.port.postMessage({activity:'start'});}
          if(this.silentFrames>=15)this.speaking=false;
          this.port.postMessage(this.frame.buffer,[this.frame.buffer]);this.frame=new Int16Array(320);this.used=0;
        }
      }
      this.previous=current;
    }
    return true;
  }
}
registerProcessor('jeff-microphone',JeffMicrophone);
