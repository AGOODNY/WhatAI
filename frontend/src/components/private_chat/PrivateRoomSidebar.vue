<template>
    <div class="sidebar">
        <div class="title">私聊列表</div>

        <button class="new-chat-btn" @click="$emit('new-chat')">
            + 新私聊
        </button>

        <div
            v-for="room in rooms"
            :key="room.id"
            role="button"
            tabindex="0"
            class="room-item"
            :class="{ active: room.id === currentRoomId }"
            @click="selectRoom(room)"
            @keydown.enter.prevent="selectRoom(room)"
            @keydown.space.prevent="selectRoom(room)"
            @mousedown.right.prevent.stop="openMenu($event, room)"
            @mouseup.right.prevent.stop="openMenu($event, room)"
            @contextmenu.prevent.stop="openMenu($event, room)"
        >
            <img :src="room.persona?.avatar_url || '/avatars/default.jpg'" />
            <span>{{ room.title }}</span>
        </div>
    </div>

    <Teleport to="body">
        <div
            v-if="menu.visible"
            class="private-room-context-menu"
            :style="{ top: menu.y + 'px', left: menu.x + 'px' }"
            @click.stop
            @mousedown.stop
            @contextmenu.prevent.stop
        >
            <button class="private-room-menu-item" type="button" @click="deleteRoom">
                删除私聊
            </button>
        </div>
    </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue"

const props = defineProps({
    rooms: Array,
    currentRoomId: Number,
})

const emit = defineEmits(["select", "new-chat", "delete-room"])

const menu = ref({
    visible: false,
    x: 0,
    y: 0,
    room: null,
})

function openMenu(e, room) {
    const menuWidth = 148
    const menuHeight = 54
    const padding = 12

    menu.value = {
        visible: true,
        x: Math.min(e.clientX, window.innerWidth - menuWidth - padding),
        y: Math.min(e.clientY, window.innerHeight - menuHeight - padding),
        room,
    }
}

function selectRoom(room) {
    emit("select", room)
}

function deleteRoom() {
    if (!menu.value.room) return

    emit("delete-room", menu.value.room)
    menu.value.visible = false
}

function closeMenu() {
    menu.value.visible = false
}

onMounted(() => {
    window.addEventListener("click", closeMenu)
    window.addEventListener("resize", closeMenu)
    window.addEventListener("scroll", closeMenu, true)
})

onUnmounted(() => {
    window.removeEventListener("click", closeMenu)
    window.removeEventListener("resize", closeMenu)
    window.removeEventListener("scroll", closeMenu, true)
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

.title {
    padding: 4px 4px 10px;
    font-size: 18px;
    font-weight: 900;
    color: #4c4038;
    border-bottom: 1px solid rgba(249, 140, 83, 0.18);
}

.new-chat-btn,
.room-item {
    width: 100%;
    border-radius: 16px;
    cursor: pointer;
}

.new-chat-btn {
    padding: 13px 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: white;
    font-weight: 900;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.23);
}

.room-item {
    padding: 10px 12px;
    border: 1px solid rgba(171, 215, 251, 0.35);
    background: rgba(249, 242, 239, 0.78);
    color: var(--color-text);
    display: flex;
    align-items: center;
    gap: 10px;
    text-align: left;
    transition:
        transform 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        background-color 0.2s ease;
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
}

img {
    width: 36px;
    height: 36px;
    flex: 0 0 auto;
    border-radius: 50%;
    object-fit: cover;
}

span {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 800;
}

:global(.private-room-context-menu) {
    position: fixed;
    min-width: 148px;
    padding: 8px;
    background: rgba(255, 255, 255, 0.98);
    color: var(--color-text);
    border: 1px solid var(--color-border);
    border-radius: 16px;
    box-shadow: 0 18px 45px rgba(164, 109, 78, 0.2);
    z-index: 9999;
}

:global(.private-room-menu-item) {
    width: 100%;
    min-height: 38px;
    padding: 9px 12px;
    border-radius: 12px;
    background: transparent;
    color: #b76343;
    cursor: pointer;
    font-size: 14px;
    font-weight: 800;
    text-align: left;
    transition:
        background-color 0.2s ease,
        color 0.2s ease;
}

:global(.private-room-menu-item:hover) {
    background: rgba(252, 206, 180, 0.48);
    color: #8f3f25;
}
</style>
