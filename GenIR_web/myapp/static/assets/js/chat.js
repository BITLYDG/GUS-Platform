let citations;
let cntQuery = 0;
let cntResponse = 0;
let isUpload = 0;
let conversationHistory = []
const newChatButton = document.getElementById('new-chat-btn');
if (newChatButton) {
    newChatButton.addEventListener('click', () => {
        console.log('New Chat Button clicked!');
        if (isUpload) {
            chatMessages.innerHTML = '';
            cntQuery = 0;
            cntResponse = 0;
            conversationHistory = []
            TrackingController.resetAllData();
        } else {
            showPopup()
        }
    });
}
const newChatButton1 = document.getElementById('new-chat-btn1');
if (newChatButton1) {
    newChatButton1.addEventListener('click', () => {
        console.log('New Chat Button clicked!');
        if (isUpload) {
            chatMessages.innerHTML = '';
            cntQuery = 0;
            cntResponse = 0;
            conversationHistory = []
            TrackingController.resetAllData();
        } else {
            showPopup()
        }
    });
}


function showPopup() {
    var overlay = document.getElementById("overlay");
    overlay.style.display = "block";
}

function clearButNoUpload() {
    var overlay = document.getElementById("overlay");
    chatMessages.innerHTML = '';
    cntQuery = 0;
    cntResponse = 0;
    conversationHistory = []
    TrackingController.resetAllData();
    overlay.style.display = "none";
}

function clearAndUpload() {
    var overlay = document.getElementById("overlay");
    chatMessages.innerHTML = '';
    cntQuery = 0;
    cntResponse = 0;
    conversationHistory = []
    TrackingController.handleDataUpload();
    TrackingController.resetAllData();
    overlay.style.display = "none";
}

function cancel() {
    var overlay = document.getElementById("overlay");
    overlay.style.display = "none";
}

const botResponses = [
    "Hello! How can I assist you today?",
    "I'm here to help! What do you need?",
    "Good day! How can I support you?",
    "I'm a bot, but I can help you find what you're looking for.",
    "Can you clarify that a bit more?",
    "I'm sorry, I didn't understand. Could you please rephrase?"
];
// 获取 DOM 元素
const chatMessages = document.getElementById('chat-messages');
const userMessageInput = document.getElementById('user-message');
const sendBtn = document.getElementById('send-btn');

// 当前时间，模拟用户消息的发送时间
function getCurrentTime() {
    const date = Date.now();
    // let hours = date.getHours();
    // let minutes = date.getMinutes();
    // const ampm = hours >= 12 ? 'PM' : 'AM';
    // hours = hours % 12;
    // hours = hours ? hours : 12; // 12 hours format
    // minutes = minutes < 10 ? '0' + minutes : minutes;
    // return `${hours}:${minutes} ${ampm}`;
    return date
}

function updateBotMessageWithMarkdown(botMessageElement, content) {
    // 使用 marked 将接收到的内容转换为 HTML 格式
    //const htmlContent = marked.parse(content);
    // 更新现有消息框的内容
    botMessageElement.querySelector('.message-content').innerHTML += content;
}

function addMessage(content, sender) {

    // 确保消息内容和发送者不为空
    if (!content || !sender) return null;

    const messageElement = document.createElement('li');
    messageElement.classList.add('d-flex', 'message');
    if (sender === 'user') {
        messageElement.classList.add('right');
    }

    const messageBody = document.createElement('div');
    messageBody.classList.add('message-body');

    // 日期时间
    // const dateTime = document.createElement('span');
    // dateTime.classList.add('date-time', 'text-muted');
    // dateTime.innerHTML = `${getCurrentTime()} <i class="zmdi zmdi-check-all text-primary"></i>`;

    // 消息内容
    const messageRow = document.createElement('div');
    messageRow.classList.add('message-row', 'd-flex', 'align-items-center');
    if (sender === 'user') {
        messageRow.classList.add('justify-content-end');
    }

    // 操作按钮
    const dropdown = document.createElement('div');
    dropdown.classList.add('dropdown');
    const dropdownLink = document.createElement('a');
    dropdownLink.classList.add('text-muted', 'me-1', 'p-2', 'text-muted');
    dropdownLink.setAttribute('href', '#');
    dropdownLink.setAttribute('data-toggle', 'dropdown');
    dropdownLink.setAttribute('aria-haspopup', 'true');
    dropdownLink.setAttribute('aria-expanded', 'false');
    dropdownLink.innerHTML = `<i class="zmdi zmdi-more-vert"></i>`;
    const dropdownMenu = document.createElement('div');
    dropdownMenu.classList.add('dropdown-menu');
    dropdownMenu.innerHTML = `
        <a class="dropdown-item" href="#">Edit</a>
        <a class="dropdown-item" href="#">Share</a>
        <a class="dropdown-item" href="#">Delete</a>
    `;
    dropdown.appendChild(dropdownLink);
    dropdown.appendChild(dropdownMenu);

    // 消息内容
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content', 'border', 'p-3');
    messageContent.innerHTML = content;
    if (sender === 'user') {
        messageContent.id = "Query" + (cntQuery++);
    } else {
        messageContent.id = "Response" + (cntResponse++);
    }
    messageRow.appendChild(dropdown);
    messageRow.appendChild(messageContent);

    // messageBody.appendChild(dateTime);
    messageBody.appendChild(messageRow);
    messageElement.appendChild(messageBody);

    chatMessages.appendChild(messageElement);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 返回消息元素，以便后续更新
    return messageElement;
}

// 生成随机的机器人回复
function getRandomBotResponse() {
    const randomIndex = Math.floor(Math.random() * botResponses.length);
    return botResponses[randomIndex];
}

// 发送按钮点击事件
sendBtn.addEventListener('click', () => {
    const userMessage = userMessageInput.value.trim();
    isUpload = 0;
    if (userMessage) {
        // 用户消息
        addMessage(userMessage, 'user');
        userMessageInput.value = ''; // 清空输入框
        callPerplexityAPI(userMessage)
        setTimeout(() => {
            const botResponse = getRandomBotResponse();
            //addMessage(botResponse, 'bot');
        }, 1000); // 模拟延迟
    }
});

// 支持按回车键发送消息
userMessageInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendBtn.click();
    }
});

function getInputValues(userMessage) {
    // 获取所有 input 的值
    conversationHistory.push({
        content: userMessage,
        role: "user"
    });
    const model = "llama-3.1-sonar-small-128k-online";
    const max_tokens = 4096;
    const presence_penalty = 0;
    const return_images = false; // 转为布尔值
    const temperature = 0.2;
    const return_related_questions = false // 转为布尔值
    const stream = true; // 转为布尔值
    const top_k = 0;
    const top_p = 0.9;

    // 将值组合成对象
    const options = {
        conversationHistory,
        model,
        max_tokens,// 转为整数
        presence_penalty, // 转为浮点数
        return_images,
        temperature,
        return_related_questions,
        stream,
        top_k,
        top_p,
    };
    // console.log(options);
    return options;
}

// 假设你已经在页面中引入了 Marked 库
async function callPerplexityAPI(userMessage) {
    const options = getInputValues(userMessage);

    const response = await fetch("/api/perplexity/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(options)
    });

    if (response.ok) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let done = false;
        let partialMessage = "";  // 用于拼接流式数据

        // 创建初始的消息框
        let botMessageElement = addMessage(" ", "bot");  // 先添加一个空的消息元素，并获得该元素的引用
        let messageContentElement = botMessageElement.querySelector('.message-content');
        let fullMarkdownText = "";

        // 读取流数据并逐步拼接消息
        while (!done) {
            const {value, done: streamDone} = await reader.read();
            done = streamDone;

            if (value) {
                const chunk = decoder.decode(value);
                partialMessage += chunk;
                // 将收到的内容按照行拆分，注意最后可能存在不完整的一行
                const lines = partialMessage.split("\n");
                partialMessage = lines.pop();  // 保留最后不完整的一行

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const jsonString = line.slice(6); // 去掉 "data: " 前缀
                            const jsonData = JSON.parse(jsonString);
// 获取 Markdown 内容
                            const botContent = jsonData.choices[0].delta.content || "";

// 获取引用链接
                            citations = jsonData.citations || [];

// 处理 Markdown 内容，替换 [n] 为超链接
                            let processedContent = botContent.replace(/\[(\d+)\]/g, (match, number) => {
                                const citationIndex = parseInt(number) - 1;
                                if (citations[citationIndex]) {
                                    return `<a href="${citations[citationIndex]}" target="_blank">${match}</a>`;
                                }
                                return match;  // 如果没有对应的引用链接，返回原始的 [1] 等文本
                            });
                            fullMarkdownText += processedContent;
                            messageContentElement.innerHTML = marked.parse(fullMarkdownText);
                            const links = messageContentElement.querySelectorAll("a");
                            links.forEach(link => {
                                if (!link.hasAttribute("target")) {
                                    link.setAttribute("target", "_blank");
                                }
                            });
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } catch (error) {
                            console.error("JSON解析失败：", error);
                        }
                    }
                }
            }
        }
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if (Array.isArray(citations)) {
            let cnt = 0;
            citations.forEach(citation => {
                cnt++;
                messageContentElement.innerHTML += `<br>[${cnt}]: <a href="${citation}" target="_blank">${citation}</a>`;
            });
        }
        conversationHistory.push({
            content: messageContentElement.innerHTML,
            role: "assistant"
        });
        // console.log(chatMessages.scrollTop)
        // console.log(chatMessages.scrollHeight)
        chatMessages.scrollTop = chatMessages.scrollHeight;
        // console.log(chatMessages.scrollTop)
        // Trigger response tracking after the stream is complete
        // Use a minimal delay to ensure the DOM is updated
        requestAnimationFrame(() => {
            const responseElement = messageContentElement;
            if (responseElement && !DialogueTracker.processedResponses.has(responseElement.id)) {
                DialogueTracker.processedResponses.add(responseElement.id);
                const responseHTML = responseElement.innerHTML;
                if (responseHTML) {
                    DialogueTracker.recordResponse(responseHTML);
                    if (CONFIG.debug) console.log("输出完毕后自动识别到响应:", responseHTML);
                }
            }
        });
    } else {
        console.error("API请求失败：");
    }
}