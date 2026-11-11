/**
 * Browser microphone recorder.
 * MediaRecorder produces WebM/Opus; the server converts it to PCM/16 kHz.
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
    this.stream = null;
    this.silenceTimer = null;
    this.isRecording = false;
  }

  async start() {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Microphone capture is not supported by this browser.");
    }

    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass();

    const source = this.audioContext.createMediaStreamSource(this.stream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 2048;
    source.connect(this.analyser);

    const mimeCandidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      ""
    ];
    const mimeType = mimeCandidates.find(
      (type) => !type || MediaRecorder.isTypeSupported(type)
    );

    this.mediaRecorder = mimeType
      ? new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined)
      : new MediaRecorder(this.stream);

    this.audioChunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) this.audioChunks.push(event.data);
    };

    this.mediaRecorder.onstop = async () => {
      const blob = new Blob(this.audioChunks, {
        type: this.mediaRecorder.mimeType || "audio/webm"
      });

      this.stream?.getTracks().forEach((track) => track.stop());
      this.stream = null;

      try {
        await this.onUtterance?.(blob);
      } finally {
        this.audioChunks = [];
      }
    };

    this.mediaRecorder.start();
    this.isRecording = true;
    this._monitorSilence();
  }

  stop() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
    }
    this.isRecording = false;
    clearTimeout(this.silenceTimer);
    this.silenceTimer = null;

    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
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

      // Timer runs during silence, not during speech.
      if (rms <= this.silenceThreshold) {
        if (!this.silenceTimer) {
          this.silenceTimer = setTimeout(
            () => this.stop(),
            this.silenceTimeoutMs
          );
        }
      } else {
        clearTimeout(this.silenceTimer);
        this.silenceTimer = null;
      }

      if (this.isRecording) requestAnimationFrame(checkLevel);
    };

    this.silenceTimer = setTimeout(
      () => this.stop(),
      this.silenceTimeoutMs
    );
    requestAnimationFrame(checkLevel);
  }
}
