<!-- 文件：src/components/ChatWindow.vue -->
<template>
    <div class="chat-area">
        <div class="chat-header">
            当前聊天：{{ roomName }}
        </div>

        <div class="chat-content" ref="chatContentRef">
            <!-- 未选择房间 -->
            <div v-if="!roomId">
                请选择一个聊天
            </div>

            <!-- 消息列表 -->
            <MessageItem
                v-for="msg in messages"
                :key="msg.id"
                :role="msg.role"
                :content="msg.content"
            />
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onUnmounted, onMounted, nextTick } from "vue"
import axios from "axios"
import MessageItem from "./MessageItem.vue"

/**
 * 接收当前房间ID
 */
const props = defineProps({
    roomId: Number
})

/**
 * 房间名称
 */
const roomName = ref("未选择")

/**
 * 消息列表
 */
const messages = ref([])

/**
 * DOM 引用
 */
const chatContentRef = ref(null)

/**
 * 是否在底部（新增）
 */
const isAtBottom = ref(true)

/**
 * 记录最新消息ID
 */
const lastId = ref(null)

/**
 * 轮询定时器
 */
let timer = null

/**
 * 判断是否在底部（新增）
 */
function checkIfAtBottom() {
    const el = chatContentRef.value
    if (!el) return

    const threshold = 50 // 容忍误差（像微信一样）
    isAtBottom.value =
        el.scrollHeight - el.scrollTop - el.clientHeight < threshold
}

/**
 * 平滑滚动到底部（修改）
 */
async function scrollToBottom(force = false) {
    await nextTick()

    const el = chatContentRef.value
    if (!el) return

    // 只有在底部 或 强制滚动 才滚
    if (isAtBottom.value || force) {
        el.scrollTo({
            top: el.scrollHeight,
            behavior: "smooth"
        })
    }
}

/**
 * 获取房间名称
 */
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
        console.error("获取房间名失败:", err)
        roomName.value = "加载失败"
    }
}

/**
 * 获取初始消息
 */
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

        // 初始加载 → 强制滚到底
        scrollToBottom(true)

    } catch (err) {
        console.error("获取消息失败:", err)
    }
}

/**
 * 拉取新增消息
 */
async function fetchNewMessages() {
    if (!props.roomId || !lastId.value) return

    try {
        const res = axios.get(`/api/chat/rooms/${props.roomId}/messages/?last_id=${lastId.value}`)

        const newMsgs = res.data

        if (newMsgs.length > 0) {
            messages.value.push(...newMsgs)
            lastId.value = newMsgs[newMsgs.length - 1].id

            // 只有在底部才滚
            scrollToBottom()
        }

    } catch (err) {
        console.error("获取新消息失败:", err)
    }
}

/**
 * 启动轮询
 */
function startPolling() {
    stopPolling()

    timer = setInterval(() => {
        fetchNewMessages()
    }, 3000)
}

/**
 * 停止轮询
 */
function stopPolling() {
    if (timer) {
        clearInterval(timer)
        timer = null
    }
}

/**
 * 监听 roomId 变化
 */
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

/**
 * 监听滚动（新增）
 */
onMounted(() => {
    const el = chatContentRef.value
    if (el) {
        el.addEventListener("scroll", checkIfAtBottom)
    }
})

/**
 * 组件卸载清理
 */
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
    display: flex;
    flex-direction: column;
}

.chat-header {
    height: 60px;
    background: white;
    border-bottom: 1px solid #ddd;
    display: flex;
    align-items: center;
    padding: 0 20px;
    font-weight: bold;
}

.chat-content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
}

.message-item {
    margin-bottom: 10px;
}
</style>