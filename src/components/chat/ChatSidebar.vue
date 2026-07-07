<template>
    <div class="sidebar">
        <div class="sidebar-header">
            聊天列表
        </div>

        <div
            v-for="room in rooms"
            :key="room.id"
            class="room-item"
            :class="[
                { active: room.id === currentRoomId },
                { paused: !room.is_active }
            ]"
            @click="handleSelect(room.id)"
            @contextmenu.prevent="openMenu($event, room)"
        >
            <div class="room-name">
                {{ room.name }}
            </div>

            <div v-if="!room.is_active" class="paused-tag">
                已暂停
            </div>
        </div>

        <div class="create-btn" @click="handleCreate">
            + 新建聊天
        </div>

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
import axios from "@/api/axios"
import { useRouter } from "vue-router"

const props = defineProps({
    currentRoomId: Number
})

const emit = defineEmits(["selectRoom", "createRoom"])

const router = useRouter()

const rooms = ref([])

const menu = ref({
    visible: false,
    x: 0,
    y: 0,
    room: null
})

async function fetchRooms() {
    try {
        const res = await axios.get("/api/chat/rooms/")
        rooms.value = res.data

        console.log("房间列表:", rooms.value)
    } catch (err) {
        console.error("获取聊天列表失败:", err)
    }
}

function handleSelect(id) {
    emit("selectRoom", id)
}

function openMenu(e, room) {
    menu.value = {
        visible: true,
        x: e.clientX,
        y: e.clientY,
        room
    }
}

async function deleteRoom(room) {
    try {
        await axios.delete(`/api/chat/rooms/${room.id}/delete/`)

        menu.value.visible = false
        fetchRooms()

    } catch (err) {
        console.error("删除失败:", err)
    }
}

async function toggleRoom(room) {
    try {
        const res = await axios.post(`/api/chat/rooms/${room.id}/toggle/`)

        room.is_active = res.data.is_active

        menu.value.visible = false

    } catch (err) {
        console.error("切换失败:", err)
    }
}

function handleCreate() {
    router.push("/create")
}

onMounted(() => {
    fetchRooms()

    window.addEventListener("click", () => {
        menu.value.visible = false
    })
})
</script>

<style scoped>
.sidebar {
    width: clamp(220px, 24vw, 300px);
    flex: 0 0 clamp(220px, 24vw, 300px);
    min-width: 0;
    min-height: 0;
    padding: 16px;
    background: rgba(255, 255, 255, 0.78);
    color: var(--color-text);
    display: flex;
    flex-direction: column;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
    overflow-x: hidden;
    overflow-y: auto;
}

.sidebar-header {
    padding: 4px 4px 10px;
    font-size: 18px;
    font-weight: 800;
    color: #4c4038;
    border-bottom: 1px solid rgba(249, 140, 83, 0.18);
}

.room-item {
    padding: 13px 14px;
    border: 1px solid rgba(171, 215, 251, 0.35);
    border-radius: 16px;
    background: rgba(249, 242, 239, 0.78);
    cursor: pointer;
    display: flex;
    gap: 10px;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 20px rgba(164, 109, 78, 0.06);
    transition:
        background-color 0.2s ease,
        border-color 0.2s ease,
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.room-item:hover {
    background: #fffaf7;
    border-color: rgba(249, 140, 83, 0.34);
    box-shadow: 0 12px 24px rgba(249, 140, 83, 0.12);
    transform: translateY(-1px);
}

.room-item.active {
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.95), rgba(171, 215, 251, 0.6));
    border-color: rgba(249, 140, 83, 0.55);
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.17);
}

.room-item.paused {
    background: rgba(210, 224, 170, 0.32);
    color: var(--color-muted);
}

.room-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 14px;
    font-weight: 700;
}

.paused-tag {
    flex: 0 0 auto;
    padding: 3px 8px;
    border-radius: 999px;
    background: rgba(210, 224, 170, 0.65);
    color: #7c8d3d;
    font-size: 12px;
    font-weight: 700;
}

.create-btn {
    margin-top: auto;
    padding: 13px 16px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: #fff;
    text-align: center;
    cursor: pointer;
    font-size: 14px;
    font-weight: 800;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.23);
    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        filter 0.2s ease;
}

.create-btn:hover {
    filter: saturate(1.05);
    box-shadow: 0 16px 30px rgba(249, 140, 83, 0.3);
    transform: translateY(-1px);
}

.context-menu {
    position: fixed;
    min-width: 150px;
    padding: 6px;
    background: rgba(255, 255, 255, 0.96);
    color: var(--color-text);
    border: 1px solid var(--color-border);
    border-radius: 14px;
    box-shadow: var(--shadow-card);
    z-index: 1000;
    overflow: hidden;
}

.context-menu div {
    padding: 10px 12px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 14px;
}

.context-menu div:hover {
    background: rgba(252, 206, 180, 0.5);
}

@media (max-width: 760px) {
    .sidebar {
        width: 100%;
        flex: 0 0 auto;
        max-height: 34dvh;
        padding: 12px;
        border-radius: 18px;
    }

    .sidebar-header {
        font-size: 16px;
        padding-bottom: 8px;
    }

    .room-item {
        padding: 11px 12px;
    }

    .create-btn {
        margin-top: 2px;
        padding: 12px;
    }
}

@media (max-width: 520px) {
    .sidebar {
        max-height: 30dvh;
    }
}
</style>
