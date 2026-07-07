<template>
    <div class="sidebar">
        <div class="title">私聊列表</div>

        <button class="new-chat-btn" @click="$emit('new-chat')">
            + 新私聊
        </button>

        <button
            v-for="room in rooms"
            :key="room.id"
            class="room-item"
            :class="{ active: room.id === currentRoomId }"
            @click="$emit('select', room)"
        >
            <img :src="room.persona?.avatar_url || '/avatars/default.jpg'" />
            <span>{{ room.title }}</span>
        </button>
    </div>
</template>

<script setup>
defineProps({
    rooms: Array,
    currentRoomId: Number,
})

defineEmits(["select", "new-chat"])
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
</style>
