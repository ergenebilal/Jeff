/* Resample the actual capture rate to 16 kHz; transfer 20 ms PCM frames. */
class JeffMicrophone extends AudioWorkletProcessor {
  constructor(){super();this.phase=0;this.total=0;this.previous=0;this.frame=new Int16Array(320);this.used=0;}
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
          this.port.postMessage(this.frame.buffer,[this.frame.buffer]);this.frame=new Int16Array(320);this.used=0;
        }
      }
      this.previous=current;
    }
    return true;
  }
}
registerProcessor('jeff-microphone',JeffMicrophone);
