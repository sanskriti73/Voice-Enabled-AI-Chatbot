async function sendMessage() {
    const input = document.getElementById("message");
    const chatbot = document.getElementById("chat-box");
    const message = input.ariaValueMax.trim();
    if (message === "") return;
    chatBox.innerHTML += <p><b>You:</b>${message}</p>;
    const response = await
    fetch("/chat",{
        method: "POST",
        headers: {
            "content-Type": "application/JSON"
        },
        body: JSON.stringify({
            message: message
        })
    });
    const data = await
    response.json();

    chatBox.innerHTML += '<p><b>Bot:</b>${data.reply}</p>';
    input.value = "";
}