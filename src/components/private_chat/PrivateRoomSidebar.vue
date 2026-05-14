<template>
    <div class="sidebar">

        <div class="title">
            私聊列表
        </div>

        <div
            class="new-chat-btn"
            @click="$emit('new-chat')"
        >
            + 新私聊
        </div>

        <div
            v-for="room in rooms"
            :key="room.id"
            class="room-item"
            :class="{
                active: room.id === currentRoomId
            }"
            @click="$emit('select', room)"
        >
            {{ room.title }}
        </div>

    </div>
</template>

<script setup>
defineProps({
    rooms: Array,
    currentRoomId: Number,
})

defineEmits([
    "select",
    "new-chat"
])
</script>

<style scoped>
.sidebar{
    width:260px;
    background:#2f3136;
    color:white;
    overflow-y:auto;
    display:flex;
    flex-direction:column;
}

.title{
    padding:20px;
    font-size:18px;
    font-weight:bold;
}

.new-chat-btn{
    margin:0 16px 16px;
    padding:12px;
    border-radius:10px;
    background:#5865f2;
    text-align:center;
    cursor:pointer;
}

.new-chat-btn:hover{
    background:#4752c4;
}

.room-item{
    padding:14px 20px;
    cursor:pointer;
}

.room-item:hover{
    background:#40444b;
}

.room-item.active{
    background:#5865f2;
}
</style>