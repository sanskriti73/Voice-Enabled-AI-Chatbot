/**
 * static/recorder.js
 * Thin wrapper around the browser MediaRecorder API used to capture
 * microphone audio and stream a complete utterance to the Flask backend
 * over Socket.IO once the user stops speaking (client-side silence
 * detection using the Web Audio API's AnalyserNode).
 */
 
class VoiceRecorder {
    constructor({ onUtterance, silenceThreshold = 0.02, silenceTimeoutMs = 1200 } = {}) {
        this.onUtterance = onUtterance;
        this.silenceThreshold = silenceThreshold;
        this.silenceTimeoutMs = silenceTimeoutMs;
 
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.analyser = null;
        this.silenceTimer = null;
        this.isRecording = false;
    }
 
    async start() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
 
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = this.audioContext.createMediaStreamSource(stream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 2048;
        source.connect(this.analyser);
 
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
 
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) this.audioChunks.push(event.data);
        };
 
        this.mediaRecorder.onstop = () => {
            const blob = new Blob(this.audioChunks, { type: "audio/webm" });
            stream.getTracks().forEach((track) => track.stop());
            if (this.onUtterance) this.onUtterance(blob);
        };
 
        this.mediaRecorder.start();
        this.isRecording = true;
        this._monitorSilence();
    }
 
    stop() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
        clearTimeout(this.silenceTimer);
        if (this.audioContext) this.audioContext.close();
    }
 
    _monitorSilence() {
        const buffer = new Uint8Array(this.analyser.fftSize);
 
        const checkLevel = () => {
            if (!this.isRecording) return;
            this.analyser.getByteTimeDomainData(buffer);
 
            let sumSquares = 0;
            for (const sample of buffer) {
                const normalized = sample / 128 - 1;
                sumSquares += normalized * normalized;
            }
            const rms = Math.sqrt(sumSquares / buffer.length);
 
            if (rms > this.silenceThreshold) {
                clearTimeout(this.silenceTimer);
                this.silenceTimer = setTimeout(() => this.stop(), this.silenceTimeoutMs);
            }
            if (this.isRecording) requestAnimationFrame(checkLevel);
        };
 
        this.silenceTimer = setTimeout(() => this.stop(), this.silenceTimeoutMs);
        requestAnimationFrame(checkLevel);
    }
}
 
