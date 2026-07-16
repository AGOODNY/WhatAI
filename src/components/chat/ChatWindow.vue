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
                :role="msg.role"
                :persona="msg.persona"
                :content="msg.content"
            />
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onUnmounted, onMounted, nextTick } from "vue"
import axios from "@/api/axios"
import MessageItem from "./MessageItem.vue"

const props = defineProps({
    roomId: Number
})

const roomName = ref("未选择")
const messages = ref([])
const chatContentRef = ref(null)
const isAtBottom = ref(true)
const lastId = ref(null)

let timer = null
let isFetchingNew = false

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
        return
    }

    try {
        const res = await axios.get(
            "/api/chat/rooms/"
        )

        const room = res.data.find(r => r.id === props.roomId)
        roomName.value = room ? room.name : "未知房间"

    } catch (err) {
        console.error("获取房间名称失败", err)
        roomName.value = "加载失败"
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

                messages.value.push(newMsgs[i])
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

        await fetchRoomName()

        if (newVal) {
            await fetchMessages()
            startPolling()
        }
    },
    { immediate: true }
)

onMounted(() => {
    const el = chatContentRef.value
    if (el) {
        el.addEventListener("scroll", checkIfAtBottom)
    }
})

onUnmounted(() => {
    stopPolling()

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
}
</style>
