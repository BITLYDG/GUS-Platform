// 配置对象
var protocol = window.location.protocol;  // http 或 https
var host = window.location.hostname;
var port = window.location.port || (protocol === 'https:' ? '443' : '80');

const CONFIG = {
    baseUrl: `${protocol}//${host}:${port}/`,
    dataUrl: `${protocol}//${host}:${port}/task/data/`,
    listUrl: `${protocol}//${host}:${port}/tasks/`,
    debug: false,
    timeLimit: 10000 // 视图状态检查时间限制
};

/**
 * 对话记录模块
 * 负责记录和管理AI对话内容
 */
// 新增：获取CSRF Token的函数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const DialogueTracker = {
    currentQuery: null,
    dialogueHistory: [],
    messageObserver: null,
    processedResponses: new Set(), // 新增：用于跟踪已处理的响应

    initialize() {
        this.dialogueHistory = [];
        this.processedResponses.clear();
        this.setupMessageObserver();
        if (CONFIG.debug) console.log("DialogueTracker initialized");
    },

    setupMessageObserver() {
        if (this.messageObserver) {
            this.messageObserver.disconnect();
        }

        this.messageObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    this.processNewMessages(mutation.addedNodes);
                }
            });
        });

        const config = {
            childList: true,
            subtree: true
        };

        this.messageObserver.observe(document.body, config);
    },

    processNewMessages(nodes) {
        nodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                // 查询识别
                const queryElement = node.querySelector?.('.message-content[id^="Query"]');
                if (queryElement && !queryElement.dataset.processed) {
                    const queryText = queryElement.textContent.trim();
                    queryElement.dataset.processed = 'true';
                    this.recordQuery(queryText);
                    if (CONFIG.debug) console.log("自动识别到查询:", queryText);
                }

            }
        });
    },


    recordQuery(queryText) {
        this.currentQuery = {
            queryId: `q_${Date.now()}`,
            queryText: queryText,
            responses: [],
            timestamp: Date.now()
        };
        this.dialogueHistory.push(this.currentQuery);
        this.saveToLocalStorage();
    },

    recordResponse(responseHTML) {
        if (this.currentQuery) {
            this.currentQuery.responses.push({
                responseId: `r_${Date.now()}`,
                responseHTML: responseHTML,
                timestamp: Date.now()
            });
            this.saveToLocalStorage();
        }
    },

    saveToLocalStorage() {
        try {
            localStorage.setItem('dialogueHistory', JSON.stringify(this.dialogueHistory));
        } catch (error) {
            console.error("保存对话历史到localStorage失败:", error);
        }
    },

    loadFromLocalStorage() {
        try {
            const saved = localStorage.getItem('dialogueHistory');
            if (saved) {
                this.dialogueHistory = JSON.parse(saved);
                this.currentQuery = this.dialogueHistory[this.dialogueHistory.length - 1] || null;
            }
        } catch (error) {
            console.error("从localStorage加载对话历史失败:", error);
        }
    },

    getCurrentDialogue() {
        return this.dialogueHistory; // 修改：返回完整对话历史而不是当前对话
    },

    getAllDialogues() {
        return this.dialogueHistory;
    },

    destroy() {
        if (this.messageObserver) {
            this.messageObserver.disconnect();
            this.messageObserver = null;
        }
    }
};

/**
 * 页面行为跟踪模块
 * 负责记录用户在页面上的行为
 */
const BehaviorTracker = {
    pageData: {
        startTime: 0,
        endTime: 0,
        dwellTime: 0,
        pageViews: [],
        clicks: [],
        lastViewTime: 0,
        mouseMovements: [],
        scrollEvents: []
    },

    initialize() {
        this.resetPageData();
        this.setupEventListeners();
        if (CONFIG.debug) console.log("BehaviorTracker initialized");
    },

    resetPageData() {
        this.pageData.startTime = Date.now();
        this.pageData.endTime = this.pageData.startTime;
        this.pageData.dwellTime = 0;
        this.pageData.pageViews = [];
        this.pageData.clicks = [];
        this.pageData.mouseMovements = [];
        this.pageData.scrollEvents = [];
        this.pageData.lastViewTime = this.pageData.startTime;
    },

    setupEventListeners() {
        // 移除旧事件监听器，防止重复绑定
        document.removeEventListener("visibilitychange", this.handleVisibilityChange);
        document.removeEventListener("click", this.handleClick);
        window.removeEventListener("beforeunload", this.handleBeforeUnload);
        document.removeEventListener("mousemove", this.handleMouseMove);
        document.removeEventListener("scroll", this.handleScroll);
        // 先移除旧监听器，防止重复绑定
        window.removeEventListener("scroll", this.handleScroll);

        // 监听窗口滚动
        //window.addEventListener("scroll", this.handleScroll.bind(this), { passive: true });

        if (CONFIG.debug) console.log("滚动事件监听已绑定");

        // 绑定新事件监听器
        document.addEventListener("visibilitychange", this.handleVisibilityChange.bind(this));
        document.addEventListener("click", this.handleClick.bind(this));
        window.addEventListener("beforeunload", this.handleBeforeUnload.bind(this));
        document.addEventListener("mousemove", this.handleMouseMove.bind(this));
        document.querySelector('#chat-messages').addEventListener("scroll", this.handleScroll.bind(this), { passive: true });


        // 限制鼠标移动的记录频率，防止性能问题
        this.lastMouseMoveTime = 0;
    },

    handleVisibilityChange() {
        if (document.hidden) {
            this.recordPageExit();
        } else {
            this.recordPageEntry();
        }
    },

    handleClick(event) {
        const linkElement = event.target.closest("a");
        if (linkElement) {
            const responseElement = linkElement.closest('.message-content[id^="Response"]');
            let dialogueIndex = -1;
            let linkIndexInDialogue = -1;

            if (responseElement) {
                const responseIdMatch = responseElement.id.match(/Response(\d+)/);
                if (responseIdMatch) {
                    dialogueIndex = parseInt(responseIdMatch[1], 10);
                }

                const linksInResponse = responseElement.querySelectorAll('a');
                const linksArray = Array.from(linksInResponse);
                linkIndexInDialogue = linksArray.findIndex(link =>
                    link === linkElement &&
                    link.textContent === linkElement.textContent &&
                    link.href === linkElement.href
                );

                if (CONFIG.debug) {
                    console.log(`调试信息 - 对话索引: ${dialogueIndex}`);
                    console.log(`调试信息 - 响应中总链接数: ${linksArray.length}`);
                    console.log(`调试信息 - 点击的是第 ${linkIndexInDialogue + 1} 个链接`);
                    console.log(`调试信息 - 点击链接文本: ${linkElement.textContent}`);
                    console.log(`调试信息 - 点击链接地址: ${linkElement.href}`);
                }

            }

            const clickData = {
                timestamp: Date.now(),
                elementType: "link",
                href: linkElement.href,
                elementText: linkElement.textContent.trim(),
                coordinates: {
                    x: event.clientX,
                    y: event.clientY
                },
                dialogueContext: {
                    dialogueIndex: dialogueIndex + 1,
                    linkIndexInResponse: linkIndexInDialogue + 1,
                }
            };

            // 直接记录点击数据,不做重复检查
            this.pageData.clicks.push(clickData);
            if (CONFIG.debug) console.log("记录链接点击:", clickData);
        }
    }
    ,

    handleBeforeUnload() {
        this.recordPageExit();
    },

    handleMouseMove(event) {
        const now = Date.now();
        if (now - this.lastMouseMoveTime > 100) { // 限制记录频率，每 100ms 记录一次
            this.pageData.mouseMovements.push({
                timestamp: now,
                x: event.clientX,
                y: event.clientY
            });
            this.lastMouseMoveTime = now;
        }
    },

    handleScroll() {
        // console.log(this);
        // console.log("滚动事件监听开始");

        // 获取滚动元素
        const scrollElement = document.querySelector('#chat-messages');
        const now = Date.now();

        // 计算滚动位置，确保 scrollElement 存在
        const scrollY = scrollElement
            ? scrollElement.scrollTop
            : (window.scrollY || document.documentElement.scrollTop || document.body.scrollTop);

        if (CONFIG.debug) console.log(`滚动事件触发: scrollY=${scrollY}, timestamp=${now}`);

        this.pageData.scrollEvents.push({
            timestamp: now,
            scrollY: scrollY
        });
    }
    ,


    recordPageEntry() {
        this.pageData.lastViewTime = Date.now();
    },

    recordPageExit() {
        const exitTime = Date.now();
        const duration = exitTime - this.pageData.lastViewTime;
        if (duration > 0) { // 只在有效时长时记录
            this.pageData.pageViews.push({
                startTime: this.pageData.lastViewTime,
                endTime: exitTime,
                duration: duration
            });
            this.pageData.dwellTime += duration;
            this.pageData.endTime = exitTime;
        }
    },

    recordClick(event, linkElement) {
        const clickData = {
            timestamp: Date.now(),
            elementType: "link",
            href: linkElement.href,
            elementText: linkElement.textContent.trim(),
            coordinates: {
                x: event.clientX,
                y: event.clientY
            }
        };

        this.pageData.clicks.push(clickData);
    },

    getData() {
        return {
            ...this.pageData,
            currentUrl: window.location.href,
            pageTitle: document.title
        };
    }
};


/**
 * 数据管理模块
 * 负责数据的存储和上传
 */
const DataManager = {
    storagePrefix: 'behavior_tracking_',

    initialize() {
        if (CONFIG.debug) console.log("DataManager initialized");
    },

    storeData(data) {
        const key = this.storagePrefix + Date.now();
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return key;
        } catch (error) {
            console.error("存储数据失败:", error);
            return null;
        }
    },

    async uploadData(data) {

        const key = this.storeData(data);
        if (!key) return false;
        try {
            // 新增：获取CSRF令牌
            const csrftoken = getCookie('csrftoken');
            isUpload = 1;
            const response = await fetch(CONFIG.dataUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 新增CSRF令牌头
                    'X-CSRFToken': csrftoken
                },
                credentials: 'include',  // 新增此行
                body: JSON.stringify(data)
            });

            if (response.ok) {
                localStorage.removeItem(key);
                if (CONFIG.debug) console.log("数据上传成功");
                $('#successModal').modal('show');
                return true;
            } else {
                throw new Error(`上传失败: ${response.status}`);
            }
        } catch (error) {
            console.error("上传数据失败:", error);
            return false;
        }
    },

    async retryFailedUploads() {
        const keys = Object.keys(localStorage);
        for (let key of keys) {
            if (key.startsWith(this.storagePrefix)) {
                try {
                    const data = JSON.parse(localStorage.getItem(key));
                    await this.uploadData(data);
                } catch (error) {
                    console.error(`重试上传失败 (${key}):`, error);
                }
            }
        }
    }
};
/**
 * 主控制器
 * 协调各模块工作
 */
const TrackingController = {
    initialize() {
        // 初始化所有模块
        DialogueTracker.initialize();
        BehaviorTracker.initialize();
        DataManager.initialize();

        // 设置上传按钮事件
        const uploadButton = document.getElementById('uploadButton');
        if (uploadButton) {
            uploadButton.addEventListener('click', () => this.handleDataUpload());
        }

        const resetButton = document.getElementById('resetButton');
        if (resetButton) {
            resetButton.addEventListener('click', () => this.resetAllData());
        }

        if (CONFIG.debug) console.log("TrackingController initialized");
    },

    async handleDataUpload() {
        // 收集所有跟踪数据
        const trackingData = {
            dialogue: DialogueTracker.getCurrentDialogue(),
            behavior: BehaviorTracker.getData(),
            metadata: {
                timestamp: Date.now(),
                userAgent: navigator.userAgent
            }
        };

        // 上传数据
        const success = await DataManager.uploadData(trackingData);
        if (success) {
            console.log("数据上传成功");
        } else {
            console.error("数据上传失败");
        }
    },

    resetAllData() {
        // 停止所有观察者和监听器
        DialogueTracker.destroy();
        // 添加 BehaviorTracker 的 destroy 方法（如果需要）

        // 清空所有相关存储
        localStorage.clear(); // 改为清除全部 localStorage

        // 重置模块内部状态
        DialogueTracker.dialogueHistory = [];
        BehaviorTracker.resetPageData();

        // 重新初始化各模块
        DialogueTracker.initialize();
        BehaviorTracker.initialize();

        if (CONFIG.debug) console.log("所有记录数据已经重新初始化");

    }
};

// 页面加载完成后初始化系统
let initialized = false;
document.addEventListener('DOMContentLoaded', () => {
    if (!initialized) {
        TrackingController.initialize();
        initialized = true;
    }
});

window.recordQuery = (queryText) => DialogueTracker.recordQuery(queryText);
window.recordResponse = (responseHTML) => DialogueTracker.recordResponse(responseHTML);

window.resetTracking = () => TrackingController.resetAllData();