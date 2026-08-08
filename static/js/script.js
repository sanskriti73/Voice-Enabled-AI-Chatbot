/**
 * static/script.js
 * Chat UI logic: wires up the text input form, the microphone button,
 * and the Socket.IO connection to the Flask backend, rendering both
 * user and bot messages into the chat window.
 */
 
const socket = io();
 
const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const textInput = document.getElementById("text-input");
const micBtn = document.getElementById("mic-btn");
const statusLine = document.getElementById("status-line");
 
let recorder = null;
 
function appendMessage(text, sender) {
    const bubble = document.createElement("div");
    bubble.className = `message ${sender}`;
    bubble.textContent = text;
    chatWindow.appendChild(bubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
 
function playAudio(url) {
    if (!url) return;
    const audio = new Audio(url);
    audio.play().catch(() => {
        // Autoplay might be blocked until the user interacts with the page.
    });
}
 
// ------------------------------------------------------------------ //
// Text chat
// ------------------------------------------------------------------ //
chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = textInput.value.trim();
    if (!text) return;
 
    appendMessage(text, "user");
    textInput.value = "";
    statusLine.textContent = "Thinking...";
 
    try {
        const response = await fetch("/api/chat/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        const data = await response.json();
        appendMessage(data.reply_text, "bot");
        playAudio(data.reply_audio_url);
    } catch (err) {
        appendMessage("Sorry, something went wrong.", "bot");
    } finally {
        statusLine.textContent = "";
    }
});
 
// ------------------------------------------------------------------ //
// Voice chat
// ------------------------------------------------------------------ //
micBtn.addEventListener("click", async () => {
    if (recorder && recorder.isRecording) {
        recorder.stop();
        return;
    }
 
    recorder = new VoiceRecorder({
        onUtterance: async (blob) => {
            micBtn.classList.remove("recording");
            statusLine.textContent = "Transcribing...";
            const arrayBuffer = await blob.arrayBuffer();
            socket.emit("audio_chunk", { audio: arrayBuffer });
        },
    });
 
    await recorder.start();
    micBtn.classList.add("recording");
    statusLine.textContent = "Listening...";
});
 
socket.on("transcript", (data) => {
    appendMessage(data.text, "user");
    statusLine.textContent = "Thinking...";
});
 
socket.on("bot_reply", (data) => {
    appendMessage(data.reply_text, "bot");
    playAudio(data.reply_audio_url);
    statusLine.textContent = "";
});
 
socket.on("bot_error", (data) => {
    statusLine.textContent = data.error || "An error occurred.";
});
 
