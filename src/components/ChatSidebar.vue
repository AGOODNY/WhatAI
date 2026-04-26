<template>
    <div class="sidebar">
        <div class="sidebar-header">
            聊天列表
        </div>

        <!-- 聊天列表 -->
        <div v-for="room in rooms" :key="room.id" class="room-item" :class="{ active: room.id === currentRoomId }"
            @click="handleSelect(room.id)">
            {{ room.name }}
        </div>

        <!-- 新建聊天 -->
        <div class="create-btn" @click="handleCreate">
            + 新建聊天
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"

/**
 * 接收父组件传入的当前选中 room_id
 */
const props = defineProps({
    currentRoomId: Number
})

/**
 * 向父组件发送事件（切换聊天）
 */
const emit = defineEmits(["selectRoom", "createRoom"])

/**
 * 聊天列表
 */
const rooms = ref([])

/**
 * 获取聊天列表（调用后端 API）
 */
async function fetchRooms() {
    try {
        const res = await axios.get("http://127.0.0.1:8000/api/chat/rooms/")
        rooms.value = res.data

        console.log("房间列表:", rooms.value)
    } catch (err) {
        console.error("获取聊天列表失败:", err)
    }
}

/**
 * 点击某个聊天
 */
function handleSelect(id) {
    emit("selectRoom", id)
}

/**
 * 点击新建聊天
 */
function handleCreate() {
    emit("createRoom")
}

/**
 * 页面加载时获取数据
 */
onMounted(() => {
    fetchRooms()
})
</script>

<style scoped>
.sidebar {
    width: 250px;
    background: #2f3136;
    color: white;
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 15px;
    font-weight: bold;
    border-bottom: 1px solid #444;
}

.room-item {
    padding: 12px 15px;
    cursor: pointer;
}

.room-item:hover {
    background: #40444b;
}

.room-item.active {
    background: #5865f2;
}

.create-btn {
    margin-top: auto;
    padding: 15px;
    background: #3ba55d;
    text-align: center;
    cursor: pointer;
}

.create-btn:hover {
    background: #2d7d46;
}
</style>