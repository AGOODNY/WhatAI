<template>
    <div class="chat-area">
        <div class="chat-header">
            当前聊天：{{ roomName }}
        </div>

        <div class="chat-content" ref="chatContentRef">
            <div v-if="!roomId" class="empty-state">
                请选择一个聊天
            </div>

            <MessageItem
                v-for="msg in messages"
                :key="msg.id"
                :data-message-id="msg.id"
                :role="msg.role"
                :persona="msg.persona"
                :content="msg.content"
                :isMine="msg.is_user || msg.role === 'user'"
                :user="me"
                :replyTo="msg.reply_to"
                :canQuote="canSend"
                @openQuoteMenu="openQuoteMenu($event, msg)"
                @jumpToMessage="jumpToMessage"
            />
        </div>

        <div v-if="canSend" class="composer">
            <div v-if="selectedQuote" class="quote-bar">
                <span>
                    回复 <strong>{{ getMessageName(selectedQuote) }}</strong>
                    <small>{{ selectedQuote.content }}</small>
                </span>
                <button type="button" title="取消引用" @click="selectedQuote = null">×</button>
            </div>

            <form class="message-input" @submit.prevent="sendMessage">
                <input
                    v-model="draft"
                    maxlength="2000"
                    :disabled="isSending"
                    placeholder="输入消息，和 AI 一起聊..."
                />
                <button type="submit" :disabled="isSending || !draft.trim()">
                    {{ isSending ? "发送中" : "发送" }}
                </button>
            </form>
        </div>

        <div v-else-if="room?.user_participates && !isRoomActive" class="paused-hint">
            当前群聊已经暂停生成
        </div>

        <div v-else-if="roomId" class="spectator-hint">
            当前房间为观看模式
        </div>

        <Teleport to="body">
            <div
                v-if="quoteMenu.visible"
                class="message-context-menu"
                :style="quoteMenuStyle"
                @click.stop
            >
                <button type="button" @click="chooseQuote">
                    引用
                </button>
            </div>
        </Teleport>
    </div>
</template>

<script setup>
import { computed, ref, watch, onUnmounted, onMounted, nextTick } from "vue"
import axios from "@/api/axios"
import MessageItem from "./MessageItem.vue"

const props = defineProps({
    roomId: Number,
    roomActive: {
        type: Boolean,
        default: null,
    },
})

const roomName = ref("未选择")
const room = ref(null)
const messages = ref([])
const me = ref(null)
const draft = ref("")
const isSending = ref(false)
const selectedQuote = ref(null)
const liveRoomActive = ref(null)
const quoteMenu = ref({
    visible: false,
    x: 0,
    y: 0,
    message: null,
})
const chatContentRef = ref(null)
const isAtBottom = ref(true)
const lastId = ref(null)

let timer = null
let isFetchingNew = false

const quoteMenuStyle = computed(() => ({
    left: `${quoteMenu.value.x}px`,
    top: `${quoteMenu.value.y}px`,
}))

const isRoomActive = computed(() => {
    if (liveRoomActive.value !== null) return liveRoomActive.value
    if (props.roomActive !== null) return props.roomActive
    return room.value?.is_active !== false
})

const canSend = computed(() => (
    Boolean(room.value?.user_participates) && isRoomActive.value
))

function getMessageName(message) {
    if (message.is_user || message.role === "user") {
        return me.value?.nickname || me.value?.username || "我"
    }
    return message.persona?.name || message.role
}

function openQuoteMenu(event, message) {
    if (!canSend.value) return

    const menuWidth = 112
    const menuHeight = 50
    const padding = 10
    quoteMenu.value = {
        visible: true,
        x: Math.max(padding, Math.min(event.clientX, window.innerWidth - menuWidth - padding)),
        y: Math.max(padding, Math.min(event.clientY, window.innerHeight - menuHeight - padding)),
        message,
    }
}

function closeQuoteMenu() {
    quoteMenu.value.visible = false
}

function chooseQuote() {
    selectedQuote.value = quoteMenu.value.message
    closeQuoteMenu()
}

function jumpToMessage(messageId) {
    const target = chatContentRef.value?.querySelector(
        `[data-message-id="${messageId}"]`,
    )
    if (!target) return

    target.scrollIntoView({ behavior: "smooth", block: "center" })
    target.classList.remove("quote-highlight")
    void target.offsetWidth
    target.classList.add("quote-highlight")
}

function checkIfAtBottom() {
    const el = chatContentRef.value
    if (!el) return

    const threshold = 50
    isAtBottom.value =
        el.scrollHeight - el.scrollTop - el.clientHeight < threshold
}

async function scrollToBottom(force = false) {
    await nextTick()

    const el = chatContentRef.value
    if (!el) return

    if (isAtBottom.value || force) {
        el.scrollTo({
            top: el.scrollHeight,
            behavior: "smooth"
        })
    }
}

async function fetchRoomName() {
    if (!props.roomId) {
        roomName.value = "未选择"
        room.value = null
        return
    }

    try {
        const res = await axios.get(
            "/api/chat/rooms/"
        )

        const matchedRoom = res.data.find(r => r.id === props.roomId)
        roomName.value = matchedRoom ? matchedRoom.name : "未知房间"
        room.value = matchedRoom || null
        liveRoomActive.value = matchedRoom?.is_active ?? null

    } catch (err) {
        console.error("获取房间名称失败", err)
        roomName.value = "加载失败"
        room.value = null
    }
}

async function fetchRoomStatus() {
    if (!props.roomId) return

    const requestedRoomId = props.roomId
    try {
        const res = await axios.get(
            `/api/chat/rooms/${requestedRoomId}/status/`,
        )
        if (requestedRoomId !== props.roomId) return

        liveRoomActive.value = res.data.is_active
        if (room.value) {
            room.value.user_participates = res.data.user_participates
        }
    } catch (err) {
        console.error("获取群聊状态失败", err)
    }
}

async function fetchMe() {
    try {
        const res = await axios.get("/api/users/me/")
        me.value = res.data
    } catch (err) {
        console.error("获取用户信息失败", err)
    }
}

function appendMessage(message) {
    if (messages.value.some(item => item.id === message.id)) return
    messages.value.push(message)
    lastId.value = Math.max(lastId.value || 0, message.id)
}

async function sendMessage() {
    const content = draft.value.trim()
    if (!content || !props.roomId || isSending.value || !canSend.value) return

    const requestedRoomId = props.roomId
    isSending.value = true

    try {
        const res = await axios.post(
            `/api/chat/rooms/${requestedRoomId}/send/`,
            {
                content,
                reply_to_id: selectedQuote.value?.id || null,
            },
        )

        if (requestedRoomId !== props.roomId) return
        appendMessage(res.data)
        draft.value = ""
        selectedQuote.value = null
        await scrollToBottom(true)
    } catch (err) {
        console.error("发送群聊消息失败", err)
        if (err.response?.status === 409) {
            liveRoomActive.value = false
            closeQuoteMenu()
            alert("当前群聊已经暂停生成")
        } else {
            alert("消息发送失败，请稍后重试")
        }
    } finally {
        isSending.value = false
    }
}

async function fetchMessages() {
    if (!props.roomId) return

    try {
        const res = await axios.get(
            `/api/chat/rooms/${props.roomId}/messages/`
        )

        messages.value = res.data

        if (messages.value.length > 0) {
            lastId.value = messages.value[messages.value.length - 1].id
        }

        console.log("初始消息:", messages.value)
        scrollToBottom(true)

    } catch (err) {
        console.error("获取消息失败:", err)
    }
}

async function fetchNewMessages() {
    if (!props.roomId || isFetchingNew) return

    const requestedRoomId = props.roomId
    const requestUrl = lastId.value === null
        ? `/api/chat/rooms/${requestedRoomId}/messages/`
        : `/api/chat/rooms/${requestedRoomId}/messages/?last_id=${lastId.value}`
    isFetchingNew = true

    try {
        const res = await axios.get(requestUrl)

        if (requestedRoomId !== props.roomId) return

        const newMsgs = res.data || []

        if (!Array.isArray(newMsgs)) {
            console.error("返回数据不是数组:", newMsgs)
            return
        }

        if (newMsgs.length > 0) {
            lastId.value = newMsgs[newMsgs.length - 1].id

            for (let i = 0; i < newMsgs.length; i++) {
                if (requestedRoomId !== props.roomId) return

                appendMessage(newMsgs[i])
                await scrollToBottom()

                if (i < newMsgs.length - 1) {
                    await wait(350 + Math.floor(Math.random() * 551))
                }
            }
        }

    } catch (err) {
        console.error("获取新消息失败:", err)
    } finally {
        isFetchingNew = false
    }
}

function wait(ms) {
    return new Promise(resolve => {
        setTimeout(resolve, ms)
    })
}

function startPolling() {
    stopPolling()

    timer = setInterval(() => {
        fetchNewMessages()
        fetchRoomStatus()
    }, 3000)
}

function stopPolling() {
    if (timer) {
        clearInterval(timer)
        timer = null
    }
}

watch(
    () => props.roomId,
    async (newVal) => {
        stopPolling()

        messages.value = []
        lastId.value = null
        liveRoomActive.value = null
        draft.value = ""
        selectedQuote.value = null
        closeQuoteMenu()

        await fetchRoomName()

        if (newVal) {
            await fetchMessages()
            startPolling()
        }
    },
    { immediate: true }
)

watch(
    () => props.roomActive,
    (isActive) => {
        liveRoomActive.value = isActive
        if (isActive === false) {
            closeQuoteMenu()
        }
    },
)

onMounted(() => {
    fetchMe()
    window.addEventListener("click", closeQuoteMenu)
    window.addEventListener("resize", closeQuoteMenu)
    window.addEventListener("scroll", closeQuoteMenu, true)

    const el = chatContentRef.value
    if (el) {
        el.addEventListener("scroll", checkIfAtBottom)
    }
})

onUnmounted(() => {
    stopPolling()
    window.removeEventListener("click", closeQuoteMenu)
    window.removeEventListener("resize", closeQuoteMenu)
    window.removeEventListener("scroll", closeQuoteMenu, true)

    const el = chatContentRef.value
    if (el) {
        el.removeEventListener("scroll", checkIfAtBottom)
    }
})
</script>

<style scoped>
.chat-area {
    flex: 1;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.chat-header {
    min-height: 62px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(252, 206, 180, 0.45));
    border-bottom: 1px solid rgba(249, 140, 83, 0.18);
    display: flex;
    align-items: center;
    padding: 0 22px;
    font-size: 16px;
    font-weight: 800;
    color: #4c4038;
    flex: 0 0 auto;
}

.chat-content {
    flex: 1;
    min-height: 0;
    padding: 24px;
    overflow-y: auto;
    overflow-x: hidden;
    background:
        linear-gradient(rgba(255, 255, 255, 0.35), rgba(255, 255, 255, 0.35)),
        radial-gradient(circle at 0 0, rgba(171, 215, 251, 0.22), transparent 18rem),
        radial-gradient(circle at 100% 100%, rgba(210, 224, 170, 0.18), transparent 20rem);
}

.message-item {
    margin-bottom: 10px;
}

.empty-state {
    min-height: 100%;
    display: grid;
    place-items: center;
    padding: 28px;
    color: var(--color-muted);
    font-size: 15px;
    font-weight: 700;
    text-align: center;
}

.composer {
    flex: 0 0 auto;
    border-top: 1px solid rgba(249, 140, 83, 0.16);
    background: rgba(255, 255, 255, 0.82);
}

.quote-bar {
    min-height: 44px;
    margin: 10px 18px 0;
    padding: 8px 10px 8px 12px;
    border-left: 3px solid rgba(249, 140, 83, 0.72);
    border-radius: 9px;
    background: rgba(249, 242, 239, 0.86);
    color: #6f625a;
    display: flex;
    align-items: center;
    gap: 10px;
}

.quote-bar > span {
    min-width: 0;
    flex: 1;
    display: flex;
    align-items: baseline;
    gap: 7px;
    font-size: 12px;
}

.quote-bar strong {
    color: #b86743;
}

.quote-bar small {
    min-width: 0;
    overflow: hidden;
    color: var(--color-muted);
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.quote-bar > button {
    width: 28px;
    height: 28px;
    flex: 0 0 28px;
    border-radius: 50%;
    background: transparent;
    color: #8f8177;
    cursor: pointer;
    font-size: 20px;
    line-height: 1;
}

.message-input {
    min-height: 74px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.message-input input {
    min-width: 0;
    height: 46px;
    flex: 1;
    padding: 0 14px;
    border: 1px solid rgba(249, 140, 83, 0.22);
    border-radius: 16px;
    background: rgba(249, 242, 239, 0.72);
    color: var(--color-text);
    outline: none;
}

.message-input input:focus {
    border-color: rgba(249, 140, 83, 0.55);
    background: #fff;
    box-shadow: 0 0 0 4px rgba(252, 206, 180, 0.3);
}

.message-input button {
    height: 46px;
    min-width: 82px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: #fff;
    cursor: pointer;
    font-weight: 900;
    box-shadow: 0 12px 24px rgba(249, 140, 83, 0.22);
}

.message-input button:disabled {
    cursor: not-allowed;
    filter: grayscale(0.35);
    opacity: 0.58;
}

.spectator-hint,
.paused-hint {
    min-height: 48px;
    flex: 0 0 auto;
    border-top: 1px solid rgba(249, 140, 83, 0.13);
    background: rgba(255, 255, 255, 0.72);
    color: var(--color-muted);
    display: grid;
    place-items: center;
    font-size: 13px;
    font-weight: 700;
}

.paused-hint {
    min-height: 58px;
    background: rgba(252, 206, 180, 0.42);
    color: #a65335;
    font-weight: 900;
}

:global(.message-context-menu) {
    position: fixed;
    z-index: 10000;
    width: 112px;
    padding: 6px;
    border: 1px solid var(--color-border);
    border-radius: 13px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 16px 38px rgba(164, 109, 78, 0.2);
}

:global(.message-context-menu button) {
    width: 100%;
    min-height: 36px;
    padding: 7px 12px;
    border-radius: 9px;
    background: transparent;
    color: #5f5148;
    cursor: pointer;
    font-size: 14px;
    font-weight: 800;
    text-align: left;
}

:global(.message-context-menu button:hover) {
    background: rgba(252, 206, 180, 0.4);
}

:global(.message-item.quote-highlight .bubble) {
    animation: quote-pulse 1.2s ease;
}

@keyframes quote-pulse {
    0%,
    100% {
        box-shadow: 0 8px 20px rgba(164, 109, 78, 0.08);
    }
    35% {
        box-shadow: 0 0 0 5px rgba(249, 140, 83, 0.24);
    }
}

@media (max-width: 760px) {
    .chat-area {
        border-radius: 18px;
    }

    .chat-header {
        min-height: 54px;
        padding: 0 16px;
        font-size: 15px;
    }

    .chat-content {
        padding: 16px;
    }

    .message-input {
        min-height: 66px;
        padding: 10px 12px;
    }

    .quote-bar {
        margin: 8px 12px 0;
    }

    .message-input button {
        min-width: 68px;
    }
}
</style>
