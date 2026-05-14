<template>
    <div class="sidebar">

        <div class="title">
            私聊列表
        </div>

        <div v-for="room in rooms" :key="room.id" class="room-item" :class="{
            active: room.id === currentRoomId
        }" @click="$emit('select', room)">
            {{ room.title }}
        </div>

    </div>
</template>

<script setup>
defineProps({
    rooms: Array,
    currentRoomId: Number,
})
</script>

<style scoped>
.sidebar {
    width: 260px;
    background: #2f3136;
    color: white;
    overflow-y: auto;
}

.title {
    padding: 20px;
    font-size: 18px;
    font-weight: bold;
}

.room-item {
    padding: 14px 20px;
    cursor: pointer;
}

.room-item:hover {
    background: #40444b;
}

.room-item.active {
    background: #5865f2;
}
</style>