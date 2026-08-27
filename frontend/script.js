const API_URL = "http://127.0.0.1:5000";

const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatBox = document.getElementById("chatBox");

const newChatButton = document.getElementById("newChatButton");
const chatHistory = document.getElementById("chatHistory");

const themeButton = document.getElementById("themeButton");
const themeIcon = document.getElementById("themeIcon");
const themeText = document.getElementById("themeText");

const attachButton = document.getElementById("attachButton");
const imageInput = document.getElementById("imageInput");
const imagePreviewContainer =
    document.getElementById("imagePreviewContainer");

let currentChatId = null;
let selectedImage = null;


/* =========================================
   INITIALIZE
========================================= */

async function initializeApp() {

    loadTheme();

    try {

        const response = await fetch(`${API_URL}/chats`);

        if (!response.ok) {
            throw new Error("Could not load chats");
        }

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

        clearChat();

        addMessage(
            "Backend se connection nahi ho raha.",
            "ai-message"
        );
    }

    messageInput.focus();
}


/* =========================================
   NEW CHAT
========================================= */

async function createNewChat() {

    try {

        const response = await fetch(
            `${API_URL}/new-chat`,
            {
                method: "POST"
            }
        );

        if (!response.ok) {
            throw new Error("New chat failed");
        }

        const data = await response.json();

        currentChatId = data.chat_id;

        clearChat();

        addMessage(
            "Hello! 👋 I'm your AI assistant.\n\nHow can I help you?",
            "ai-message"
        );

        await loadChats();

        messageInput.focus();

    } catch (error) {

        console.error("New chat error:", error);

        addMessage(
            "New chat create nahi ho payi.",
            "ai-message"
        );
    }
}


/* =========================================
   LOAD CHATS
========================================= */

async function loadChats() {

    try {

        const response = await fetch(
            `${API_URL}/chats`
        );

        if (!response.ok) {
            throw new Error("Chat history failed");
        }

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


            /* =================================
               CHAT CONTENT
            ================================= */

            const title =
                document.createElement("span");

            title.className =
                "chat-history-title";

            title.textContent =
                chat.title || "New Chat";

            title.title =
                chat.title || "New Chat";


            /* =================================
               THREE DOT BUTTON
            ================================= */

            const menuButton =
                document.createElement("button");

            menuButton.className =
                "chat-menu-button";

            menuButton.type =
                "button";

            menuButton.textContent =
                "⋮";

            menuButton.title =
                "Chat options";


            /* =================================
               CHAT ITEM
            ================================= */

            chatItem.appendChild(title);
            chatItem.appendChild(menuButton);


            /* =================================
               OPEN CHAT
            ================================= */

            chatItem.addEventListener(
                "click",
                function(event) {

                    if (
                        event.target.closest(
                            ".chat-menu-button"
                        )
                    ) {
                        return;
                    }

                    openChat(chat.id);
                }
            );


            /* =================================
               THREE DOT MENU
            ================================= */

            menuButton.addEventListener(
                "click",
                function(event) {

                    event.stopPropagation();

                    showChatMenu(
                        chat,
                        menuButton
                    );
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


/* =========================================
   CHAT MENU
========================================= */

function showChatMenu(chat, button) {

    /* Remove existing menus */

    document
        .querySelectorAll(".chat-context-menu")
        .forEach(menu => menu.remove());


    const menu =
        document.createElement("div");

    menu.className =
        "chat-context-menu";


    /* =================================
       RENAME
    ================================= */

    const renameButton =
        document.createElement("button");

    renameButton.type =
        "button";

    renameButton.innerHTML =
        "✎ <span>Rename</span>";

    renameButton.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();

            menu.remove();

            renameChat(chat);
        }
    );


    /* =================================
       DELETE
    ================================= */

    const deleteButton =
        document.createElement("button");

    deleteButton.type =
        "button";

    deleteButton.className =
        "delete-chat-option";

    deleteButton.innerHTML =
        "🗑 <span>Delete</span>";

    deleteButton.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();

            menu.remove();

            deleteChat(chat);
        }
    );


    menu.appendChild(renameButton);
    menu.appendChild(deleteButton);


    document.body.appendChild(menu);


    /* =================================
       POSITION MENU
    ================================= */

    const rect =
        button.getBoundingClientRect();

    menu.style.position =
        "fixed";

    menu.style.top =
        `${rect.bottom + 4}px`;

    menu.style.left =
        `${Math.max(
            5,
            rect.right - 130
        )}px`;


    /* =================================
       CLOSE ON OUTSIDE CLICK
    ================================= */

    setTimeout(() => {

        document.addEventListener(
            "click",
            function closeMenu(event) {

                if (!menu.contains(event.target)) {

                    menu.remove();

                    document.removeEventListener(
                        "click",
                        closeMenu
                    );
                }

            }
        );

    }, 0);
}


/* =========================================
   RENAME CHAT
========================================= */

async function renameChat(chat) {

    const oldTitle =
        chat.title || "New Chat";

    const newTitle =
        prompt(
            "Enter new chat name:",
            oldTitle
        );


    /* Cancel */

    if (newTitle === null) {
        return;
    }


    const title =
        newTitle.trim();


    if (!title) {

        alert(
            "Chat name cannot be empty."
        );

        return;
    }


    if (title.length > 100) {

        alert(
            "Chat name must be less than 100 characters."
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/chats/${chat.id}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        title: title
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Rename failed"
            );
        }


        await loadChats();

    } catch (error) {

        console.error(
            "Rename chat error:",
            error
        );

        alert(
            "Chat rename nahi ho payi.\n\n" +
            error.message
        );
    }
}


/* =========================================
   DELETE CHAT
========================================= */

async function deleteChat(chat) {

    const confirmed =
        confirm(
            `Delete "${chat.title || "New Chat"}"?\n\nThis will permanently delete this chat and its messages.`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/chats/${chat.id}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Delete failed"
            );
        }


        /*
           If current chat was deleted
        */

        if (
            currentChatId === chat.id
        ) {

            currentChatId = null;

            clearChat();


            /*
               Load remaining chats
            */

            const chatsResponse =
                await fetch(
                    `${API_URL}/chats`
                );

            const chats =
                await chatsResponse.json();


            if (chats.length > 0) {

                currentChatId =
                    chats[0].id;

                await loadChats();

                await loadMessages(
                    currentChatId
                );

            } else {

                await createNewChat();
            }

        } else {

            await loadChats();
        }

    } catch (error) {

        console.error(
            "Delete chat error:",
            error
        );

        alert(
            "Chat delete nahi ho payi.\n\n" +
            error.message
        );
    }
}


/* =========================================
   OPEN CHAT
========================================= */

async function openChat(chatId) {

    currentChatId = chatId;

    clearChat();

    await loadMessages(chatId);

    await loadChats();

    messageInput.focus();
}


/* =========================================
   LOAD MESSAGES
========================================= */

async function loadMessages(chatId) {

    try {

        const response =
            await fetch(
                `${API_URL}/chats/${chatId}/messages`
            );

        if (!response.ok) {

            throw new Error(
                "Messages API failed"
            );
        }

        const messages =
            await response.json();


        if (messages.length === 0) {

            addMessage(
                "Hello! 👋 I'm your AI assistant.\n\nHow can I help you?",
                "ai-message"
            );

            return;
        }


        messages.forEach(message => {

            if (
                message.role === "user"
            ) {

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


/* =========================================
   SEND MESSAGE
========================================= */

async function sendMessage() {

    const message =
        messageInput.value.trim();


    if (
        !message &&
        !selectedImage
    ) {
        return;
    }


    if (!currentChatId) {

        await createNewChat();

        if (!currentChatId) {
            return;
        }
    }


    /* IMAGE */

    if (selectedImage) {

        await analyzeSelectedImage(
            message
        );

        return;
    }


    /* NORMAL MESSAGE */

    addMessage(
        message,
        "user-message"
    );

    messageInput.value = "";

    autoResizeTextarea();

    sendButton.disabled = true;

    addThinkingMessage();


    try {

        const response =
            await fetch(
                `${API_URL}/chat`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        chat_id:
                            currentChatId,

                        message:
                            message
                    })
                }
            );


        const data =
            await response.json();


        removeThinkingMessage();


        if (!response.ok) {

            throw new Error(
                data.details ||
                data.error ||
                "AI request failed"
            );
        }


        if (data.response) {

            addMessage(
                data.response,
                "ai-message"
            );

            await loadChats();

        } else {

            addMessage(
                "AI response nahi mila.",
                "ai-message"
            );
        }

    } catch (error) {

        removeThinkingMessage();

        console.error(
            "AI error:",
            error
        );

        addErrorMessage(
            error.message
        );

    } finally {

        sendButton.disabled = false;

        messageInput.focus();
    }
}


/* =========================================
   IMAGE UPLOAD
========================================= */

if (attachButton && imageInput) {

    attachButton.addEventListener(
        "click",
        function () {

            imageInput.click();

        }
    );
}


/* =========================================
   IMAGE SELECT
========================================= */

if (imageInput) {

    imageInput.addEventListener(
        "change",
        function () {

            const file =
                imageInput.files[0];

            if (!file) {
                return;
            }


            const allowedTypes = [
                "image/png",
                "image/jpeg",
                "image/webp"
            ];


            if (
                !allowedTypes.includes(
                    file.type
                )
            ) {

                alert(
                    "Please select a PNG, JPG or WEBP image."
                );

                imageInput.value = "";

                return;
            }


            if (
                file.size >
                10 * 1024 * 1024
            ) {

                alert(
                    "Image size must be less than 10 MB."
                );

                imageInput.value = "";

                return;
            }


            selectedImage = file;

            showImagePreview(file);
        }
    );
}


/* =========================================
   IMAGE PREVIEW
========================================= */

function showImagePreview(file) {

    if (!imagePreviewContainer) {
        return;
    }


    const imageURL =
        URL.createObjectURL(file);


    imagePreviewContainer.innerHTML = `

        <div class="image-preview">

            <img
                src="${imageURL}"
                alt="Selected image"
            >

            <div class="image-preview-info">

                <span>
                    ${escapeHtml(file.name)}
                </span>

                <button
                    type="button"
                    id="removeImageButton"
                    aria-label="Remove image"
                    title="Remove image"
                >
                    ×
                </button>

            </div>

        </div>
    `;


    const removeButton =
        document.getElementById(
            "removeImageButton"
        );


    if (removeButton) {

        removeButton.addEventListener(
            "click",
            removeSelectedImage
        );
    }
}


/* =========================================
   REMOVE IMAGE
========================================= */

function removeSelectedImage() {

    selectedImage = null;

    if (imageInput) {
        imageInput.value = "";
    }

    if (imagePreviewContainer) {
        imagePreviewContainer.innerHTML = "";
    }
}


/* =========================================
   ANALYZE IMAGE
========================================= */

async function analyzeSelectedImage(
    userText = ""
) {

    if (!selectedImage) {
        return;
    }


    const file =
        selectedImage;


    const imageMessage =
        document.createElement("div");

    imageMessage.className =
        "message user-message";


    const imageURL =
        URL.createObjectURL(file);


    imageMessage.innerHTML = `

        <div>

            <img
                src="${imageURL}"
                alt="Uploaded image"
                style="
                    max-width:260px;
                    max-height:260px;
                    border-radius:10px;
                    display:block;
                    margin-bottom:8px;
                "
            >

            ${
                userText
                    ? `<div>${escapeHtml(userText)}</div>`
                    : ""
            }

        </div>
    `;


    chatBox.appendChild(
        imageMessage
    );

    chatBox.scrollTop =
        chatBox.scrollHeight;


    messageInput.value = "";

    autoResizeTextarea();

    sendButton.disabled = true;

    addThinkingMessage();


    try {

        const formData =
            new FormData();


        formData.append(
            "image",
            file
        );


        if (userText) {

            formData.append(
                "message",
                userText
            );
        }


        const response =
            await fetch(
                `${API_URL}/analyze-image`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        removeThinkingMessage();


        if (!response.ok) {

            throw new Error(
                data.details ||
                data.error ||
                "Image analysis failed"
            );
        }


        if (data.response) {

            addMessage(
                data.response,
                "ai-message"
            );

        } else {

            addMessage(
                "Image analysis ka response nahi mila.",
                "ai-message"
            );
        }


        removeSelectedImage();

    } catch (error) {

        removeThinkingMessage();

        console.error(
            "Image analysis error:",
            error
        );

        addErrorMessage(
            error.message
        );

    } finally {

        sendButton.disabled = false;

        messageInput.focus();
    }
}


/* =========================================
   ADD MESSAGE
========================================= */

function addMessage(
    text,
    className
) {

    const message =
        document.createElement("div");

    message.className =
        "message " + className;


    if (
        className.includes(
            "ai-message"
        )
    ) {

        message.innerHTML =
            renderMarkdown(text);

    } else {

        message.textContent =
            text;
    }


    chatBox.appendChild(
        message
    );

    chatBox.scrollTop =
        chatBox.scrollHeight;
}


/* =========================================
   ERROR MESSAGE
========================================= */

function addErrorMessage(text) {

    const message =
        document.createElement("div");

    message.className =
        "message ai-message";


    message.innerHTML = `

        <div style="
            display:flex;
            align-items:flex-start;
            gap:9px;
        ">

            <span style="
                display:flex;
                align-items:center;
                justify-content:center;
                width:22px;
                height:22px;
                border-radius:50%;
                background:#f0f0f0;
                flex-shrink:0;
                font-size:12px;
            ">!</span>

            <div>

                <strong>
                    Something went wrong
                </strong>

                <div style="
                    margin-top:4px;
                    color:var(--text-secondary);
                    font-size:13px;
                ">
                    ${escapeHtml(text)}
                </div>

            </div>

        </div>
    `;


    chatBox.appendChild(
        message
    );

    chatBox.scrollTop =
        chatBox.scrollHeight;
}


/* =========================================
   MARKDOWN
========================================= */

function renderMarkdown(text) {

    if (!text) {
        return "";
    }


    const codeBlocks = [];


    let workingText =
        text.replace(
            /```([a-zA-Z0-9_+#.-]*)\s*\n?([\s\S]*?)```/g,
            function (
                match,
                language,
                code
            ) {

                const index =
                    codeBlocks.length;


                const codeId =
                    "code-" +
                    Math.random()
                        .toString(36)
                        .substring(2, 10);


                codeBlocks.push({

                    id: codeId,

                    language:
                        language || "code",

                    code:
                        code
                            .replace(/^\n/, "")
                            .replace(/\n$/, "")
                });


                return `@@CODE_BLOCK_${index}@@`;
            }
        );


    workingText =
        escapeHtml(
            workingText
        );


    workingText =
        workingText.replace(
            /^### (.*)$/gm,
            "<h3>$1</h3>"
        );


    workingText =
        workingText.replace(
            /^## (.*)$/gm,
            "<h2>$1</h2>"
        );


    workingText =
        workingText.replace(
            /^# (.*)$/gm,
            "<h1>$1</h1>"
        );


    workingText =
        workingText.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    workingText =
        workingText.replace(
            /`([^`\n]+)`/g,
            '<code class="inline-code">$1</code>'
        );


    workingText =
        workingText.replace(
            /^\s*[-*] (.*)$/gm,
            "<li>$1</li>"
        );


    workingText =
        workingText.replace(
            /((?:<li>.*<\/li>\s*)+)/g,
            "<ul>$1</ul>"
        );


    const lines =
        workingText.split("\n");


    let html = "";

    let paragraph = [];


    function flushParagraph() {

        if (
            paragraph.length === 0
        ) {
            return;
        }


        const content =
            paragraph.join("<br>");


        html +=
            `<p>${content}</p>`;


        paragraph = [];
    }


    lines.forEach(
        line => {

            const trimmed =
                line.trim();


            if (

                trimmed.startsWith(
                    "<h1>"
                ) ||

                trimmed.startsWith(
                    "<h2>"
                ) ||

                trimmed.startsWith(
                    "<h3>"
                ) ||

                trimmed.startsWith(
                    "<ul>"
                ) ||

                trimmed.startsWith(
                    "@@CODE_BLOCK_"
                )

            ) {

                flushParagraph();

                html += line;

            } else if (
                trimmed === ""
            ) {

                flushParagraph();

            } else {

                paragraph.push(
                    line
                );
            }
        }
    );


    flushParagraph();


    codeBlocks.forEach(
        (block, index) => {

            const placeholder =
                `@@CODE_BLOCK_${index}@@`;


            html =
                html.replace(
                    placeholder,
                    createCodeBlock(
                        block.id,
                        block.language,
                        block.code
                    )
                );
        }
    );


    return html;
}


/* =========================================
   CREATE CODE BLOCK
========================================= */

function createCodeBlock(
    codeId,
    language,
    code
) {

    const safeLanguage =
        escapeHtml(
            language || "code"
        );


    const safeCode =
        escapeHtml(code);


    return `

        <div class="code-block">

            <div class="code-header">

                <span class="code-language">
                    ${safeLanguage}
                </span>

                <button
                    class="copy-code-button"
                    type="button"
                    data-code-id="${codeId}"
                >
                    Copy
                </button>

            </div>

            <pre><code id="${codeId}">${safeCode}</code></pre>

        </div>
    `;
}


/* =========================================
   COPY CODE
========================================= */

async function copyCode(
    codeId,
    button
) {

    const codeElement =
        document.getElementById(
            codeId
        );


    if (!codeElement) {
        return;
    }


    const code =
        codeElement.textContent;


    try {

        await navigator.clipboard
            .writeText(code);


        if (button) {

            button.textContent =
                "Copied!";


            button.classList.add(
                "copied"
            );


            setTimeout(
                () => {

                    button.textContent =
                        "Copy";


                    button.classList.remove(
                        "copied"
                    );

                },
                1500
            );
        }

    } catch (error) {

        console.error(
            "Clipboard failed:",
            error
        );
    }
}


/* =========================================
   COPY BUTTON EVENT
========================================= */

document.addEventListener(
    "click",
    function(event) {

        const button =
            event.target.closest(
                ".copy-code-button"
            );


        if (!button) {
            return;
        }


        copyCode(
            button.dataset.codeId,
            button
        );
    }
);


/* =========================================
   ESCAPE HTML
========================================= */

function escapeHtml(text) {

    return String(text)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


/* =========================================
   THINKING
========================================= */

function addThinkingMessage() {

    const message =
        document.createElement(
            "div"
        );


    message.className =
        "message ai-message thinking-message";


    message.innerHTML = `

        <span class="thinking-dot"></span>
        <span class="thinking-dot"></span>
        <span class="thinking-dot"></span>

        <span class="thinking-text">
            My AI is thinking...
        </span>
    `;


    chatBox.appendChild(
        message
    );


    chatBox.scrollTop =
        chatBox.scrollHeight;
}


function removeThinkingMessage() {

    const thinking =
        chatBox.querySelector(
            ".thinking-message"
        );


    if (thinking) {
        thinking.remove();
    }
}


/* =========================================
   CLEAR CHAT
========================================= */

function clearChat() {

    chatBox.innerHTML = "";
}


/* =========================================
   THEME
========================================= */

function loadTheme() {

    const savedTheme =
        localStorage.getItem(
            "myai-theme"
        );


    if (
        savedTheme === "dark"
    ) {

        document.body.classList.add(
            "dark"
        );

        updateThemeUI(true);

    } else {

        document.body.classList.remove(
            "dark"
        );

        updateThemeUI(false);
    }
}


function toggleTheme() {

    const isDark =
        document.body.classList.toggle(
            "dark"
        );


    localStorage.setItem(
        "myai-theme",
        isDark
            ? "dark"
            : "light"
    );


    updateThemeUI(
        isDark
    );
}


function updateThemeUI(
    isDark
) {

    if (isDark) {

        themeIcon.textContent =
            "☀";

        themeText.textContent =
            "Light mode";

    } else {

        themeIcon.textContent =
            "☾";

        themeText.textContent =
            "Dark mode";
    }
}


/* =========================================
   TEXTAREA AUTO RESIZE
========================================= */

function autoResizeTextarea() {

    messageInput.style.height =
        "auto";


    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            160
        ) + "px";
}


/* =========================================
   BUTTON EVENTS
========================================= */

sendButton.addEventListener(
    "click",
    sendMessage
);


newChatButton.addEventListener(
    "click",
    createNewChat
);


themeButton.addEventListener(
    "click",
    toggleTheme
);


/* =========================================
   ENTER / SHIFT + ENTER
========================================= */

messageInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


messageInput.addEventListener(
    "input",
    autoResizeTextarea
);





/* =========================================
   START APP
========================================= */

initializeApp();