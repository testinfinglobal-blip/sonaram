const API_URL = "http://127.0.0.1:5000";

const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatBox = document.getElementById("chatBox");

const newChatButton = document.getElementById("newChatButton");
const chatHistory = document.getElementById("chatHistory");

let currentChatId = null;


// ============================
// Start Application
// ============================

async function initializeApp() {

    try {

        const response = await fetch(`${API_URL}/chats`);

        const chats = await response.json();

        if (chats.length > 0) {

            currentChatId = chats[0].id;

            await loadChats();

            await loadMessages(currentChatId);

        } else {

            await createNewChat();

        }

    } catch (error) {

        console.error("Initialization error:", error);

        addMessage(
            "Backend se connection nahi ho raha.",
            "ai-message"
        );
    }
}


// ============================
// Create New Chat
// ============================

async function createNewChat() {

    try {

        const response = await fetch(
            `${API_URL}/new-chat`,
            {
                method: "POST"
            }
        );

        const data = await response.json();

        currentChatId = data.chat_id;

        clearChat();

        addMessage(
            "Hello! 👋 I'm your AI assistant.\nHow can I help you?",
            "ai-message"
        );

        await loadChats();

    } catch (error) {

        console.error("New chat error:", error);

        addMessage(
            "New chat create nahi ho payi.",
            "ai-message"
        );
    }
}


// ============================
// Load Chat History
// ============================

async function loadChats() {

    try {

        const response = await fetch(
            `${API_URL}/chats`
        );

        const chats = await response.json();

        chatHistory.innerHTML = "";

        chats.forEach(chat => {

            const chatItem =
                document.createElement("div");

            chatItem.className =
                "chat-history-item";

            if (chat.id === currentChatId) {

                chatItem.classList.add("active");
            }

            chatItem.textContent =
                chat.title;

            chatItem.title =
                chat.title;

            chatItem.addEventListener(
                "click",
                function() {

                    openChat(chat.id);

                }
            );

            chatHistory.appendChild(chatItem);

        });

    } catch (error) {

        console.error(
            "Chat history error:",
            error
        );
    }
}


// ============================
// Open Existing Chat
// ============================

async function openChat(chatId) {

    currentChatId = chatId;

    clearChat();

    await loadMessages(chatId);

    await loadChats();
}


// ============================
// Load Messages
// ============================

async function loadMessages(chatId) {

    try {

        const response = await fetch(
            `${API_URL}/chats/${chatId}/messages`
        );

        const messages = await response.json();

        if (messages.length === 0) {

            addMessage(
                "Hello! 👋 I'm your AI assistant.\nHow can I help you?",
                "ai-message"
            );

            return;
        }

        messages.forEach(message => {

            if (message.role === "user") {

                addMessage(
                    message.message,
                    "user-message"
                );

            } else {

                addMessage(
                    message.message,
                    "ai-message"
                );
            }

        });

    } catch (error) {

        console.error(
            "Messages loading error:",
            error
        );

        addMessage(
            "Messages load nahi ho paaye.",
            "ai-message"
        );
    }
}


// ============================
// Send Message
// ============================

async function sendMessage() {

    const message =
        messageInput.value.trim();

    if (!message) {

        return;
    }

    if (!currentChatId) {

        await createNewChat();
    }

    addMessage(
        message,
        "user-message"
    );

    messageInput.value = "";

    sendButton.disabled = true;

    addMessage(
        "Thinking...",
        "ai-message"
    );

    try {

        const response = await fetch(
            `${API_URL}/chat`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    chat_id: currentChatId,
                    message: message
                })
            }
        );

        const data = await response.json();

        removeThinkingMessage();

        if (data.response) {

            addMessage(
                data.response,
                "ai-message"
            );

            await loadChats();

        } else {

            addMessage(
                data.error || "AI response nahi mila.",
                "ai-message"
            );
        }

    } catch (error) {

        removeThinkingMessage();

        addMessage(
            "Backend se connection nahi ho raha.",
            "ai-message"
        );

        console.error(error);

    } finally {

        sendButton.disabled = false;

        messageInput.focus();
    }
}


// ============================
// Add Message To Screen
// ============================

function addMessage(text, className) {

    const message =
        document.createElement("div");

    message.className =
        "message " + className;

    message.textContent =
        text;

    chatBox.appendChild(message);

    chatBox.scrollTop =
        chatBox.scrollHeight;
}


// ============================
// Clear Chat Screen
// ============================

function clearChat() {

    chatBox.innerHTML = "";
}


// ============================
// Remove Thinking
// ============================

function removeThinkingMessage() {

    const messages =
        chatBox.querySelectorAll(
            ".ai-message"
        );

    if (messages.length === 0) {

        return;
    }

    const lastMessage =
        messages[messages.length - 1];

    if (
        lastMessage.textContent ===
        "Thinking..."
    ) {

        lastMessage.remove();
    }
}


// ============================
// Button Events
// ============================

sendButton.addEventListener(
    "click",
    sendMessage
);


newChatButton.addEventListener(
    "click",
    createNewChat
);


// ============================
// Enter Key
// ============================

messageInput.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Enter") {

            sendMessage();
        }

    }
);


// ============================
// Start
// ============================

initializeApp();