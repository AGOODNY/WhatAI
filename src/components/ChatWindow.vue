<!-- 文件：src/components/ChatWindow.vue -->
<template>
    <div class="chat-area">
        <div class="chat-header">
            当前聊天：{{ roomName }}
        </div>

        <div class="chat-content">
            <!-- 未选择房间 -->
            <div v-if="!roomId">
                请选择一个聊天
            </div>

            <!-- 消息列表 -->
            <MessageItem v-for="msg in messages" :key="msg.id" :role="msg.role" :content="msg.content" />
        </div>
    </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from "vue"
import axios from "axios"
import MessageItem from "./MessageItem.vue"

/**
 * 接收当前房间ID + 名称
 */
const props = defineProps({
    roomId: Number,
    roomName: String
})

/**
 * 消息列表
 */
const messages = ref([])

/**
 * 记录最新消息ID（用于增量更新）
 */
const lastId = ref(null)

/**
 * 轮询定时器
 */
let timer = null

/**
 * 获取初始消息
 */
async function fetchMessages() {
    if (!props.roomId) return

    try {
        const res = await axios.get(
            `http://127.0.0.1:8000/api/chat/rooms/${props.roomId}/messages/`
        )

        messages.value = res.data

        if (messages.value.length > 0) {
            lastId.value = messages.value[messages.value.length - 1].id
        }

        console.log("初始消息:", messages.value)

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
        const res = await axios.get(
            `http://127.0.0.1:8000/api/chat/rooms/${props.roomId}/messages/?last_id=${lastId.value}`
        )

        const newMsgs = res.data

        if (newMsgs.length > 0) {
            messages.value.push(...newMsgs)
            lastId.value = newMsgs[newMsgs.length - 1].id
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

        if (newVal) {
            await fetchMessages()
            startPolling()
        }
    },
    { immediate: true }
)

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
    stopPolling()
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