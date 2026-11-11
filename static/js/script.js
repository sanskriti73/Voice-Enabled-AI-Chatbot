
const socket = io("http://127.0.0.1:5000", {
    transports: ["websocket", "polling"]
});
const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const textInput = document.getElementById("text-input");
const micBtn = document.getElementById("mic-btn");
const statusLine = document.getElementById("status-line");

let recorder = null;

function appendMessage(text, sender) {
  const bubble = document.createElement("div");
  bubble.className = `message ${sender}`;
  bubble.textContent = text || "";
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function playAudio(url) {
  if (!url) return;
  const audio = new Audio(url);
  audio.play().catch(() => {});
}

async function sendText(text) {
  const response = await fetch("/api/chat/text", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text})
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }

  appendMessage(data.reply_text, "bot");
  playAudio(data.reply_audio_url);
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = textInput.value.trim();
  if (!text) return;

  appendMessage(text, "user");
  textInput.value = "";
  statusLine.textContent = "Thinking...";

  try {
    await sendText(text);
  } catch (error) {
    appendMessage("Sorry, something went wrong.", "bot");
  } finally {
    statusLine.textContent = "";
  }
});

micBtn.addEventListener("click", async () => {
  if (recorder?.isRecording) {
    recorder.stop();
    return;
  }

  try {
    recorder = new VoiceRecorder({
      onUtterance: async (blob) => {
        micBtn.classList.remove("recording");
        statusLine.textContent = "Transcribing...";

        const arrayBuffer = await blob.arrayBuffer();
        socket.emit("audio_chunk", {
          audio: arrayBuffer,
          session_id: null
        });
      }
    });

    await recorder.start();
    micBtn.classList.add("recording");
    statusLine.textContent = "Listening...";
  } catch (error) {
    micBtn.classList.remove("recording");
    statusLine.textContent =
      "Microphone access was denied or unavailable.";
    console.error(error);
  }
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

socket.on("response", function(data) {
    console.log("BOT RESPONSE RECEIVED:", data);

    const response = data.response || data.message || data;
    addMessage(response, "bot");
});

socket.on("connect", function() {
    console.log("SOCKET CONNECTED");
});

socket.on("connect_error", function(error) {
    console.error("SOCKET ERROR:", error);
});