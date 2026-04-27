<template>
    <div class="sidebar">
        <div class="sidebar-header">
            聊天列表
        </div>

        <!-- 聊天列表 -->
        <div
            v-for="room in rooms"
            :key="room.id"
            class="room-item"
            :class="{ active: room.id === currentRoomId }"
            @click="handleSelect(room.id)"
            @contextmenu.prevent="openMenu($event, room)"
        >
            {{ room.name }}
        </div>

        <!-- 新建聊天 -->
        <div class="create-btn" @click="handleCreate">
            + 新建聊天
        </div>

        <!-- 右键菜单 -->
        <div
            v-if="menu.visible"
            class="context-menu"
            :style="{ top: menu.y + 'px', left: menu.x + 'px' }"
        >
            <div @click="deleteRoom(menu.room)">删除房间</div>
            <div @click="toggleRoom(menu.room)">
                {{ menu.room?.is_active ? "暂停生成" : "继续生成" }}
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

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

const router = useRouter()

/**
 * 聊天列表
 */
const rooms = ref([])

/**
 * 右键菜单状态
 */
const menu = ref({
    visible: false,
    x: 0,
    y: 0,
    room: null
})

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
 * 右键打开菜单
 */
function openMenu(e, room) {
    menu.value = {
        visible: true,
        x: e.clientX,
        y: e.clientY,
        room
    }
}

/**
 * 删除房间
 */
async function deleteRoom(room) {
    try {
        await axios.delete(
            `http://127.0.0.1:8000/api/chat/rooms/${room.id}/delete/`
        )

        menu.value.visible = false

        // 刷新列表
        fetchRooms()

    } catch (err) {
        console.error("删除失败:", err)
    }
}

/**
 * 暂停 / 继续
 */
async function toggleRoom(room) {
    try {
        const res = await axios.post(
            `http://127.0.0.1:8000/api/chat/rooms/${room.id}/toggle/`
        )

        room.is_active = res.data.is_active

        menu.value.visible = false

    } catch (err) {
        console.error("切换失败:", err)
    }
}

/**
 * 点击新建聊天
 */
function handleCreate() {
    router.push("/create")
}

/**
 * 页面加载时获取数据
 */
onMounted(() => {
    fetchRooms()

    // 点击空白关闭菜单
    window.addEventListener("click", () => {
        menu.value.visible = false
    })
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

/* 右键菜单 */
.context-menu {
    position: fixed;
    background: white;
    color: black;
    border: 1px solid #ddd;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
}

.context-menu div {
    padding: 10px 20px;
    cursor: pointer;
}

.context-menu div:hover {
    background: #f0f0f0;
}
</style>