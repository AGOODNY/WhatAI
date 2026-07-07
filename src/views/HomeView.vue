<template>
    <div class="app-container">
        <ChatSidebar :currentRoomId="currentRoomId" @selectRoom="selectRoom" @createRoom="goToCreate" />

        <ChatWindow :roomId="currentRoomId" :roomName="currentRoomName" />
    </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { useRouter } from "vue-router"

import ChatSidebar from "../components/chat/ChatSidebar.vue"
import ChatWindow from "../components/chat/ChatWindow.vue"

const router = useRouter()

const currentRoomId = ref(null)
const rooms = ref([])

function selectRoom(id) {
    currentRoomId.value = id
}

function goToCreate() {
    router.push("/create")
}

const currentRoomName = computed(() => {
    return currentRoomId.value
        ? `房间 ${currentRoomId.value}`
        : "未选择"
})
</script>

<style>
.app-container {
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: flex;
    gap: 16px;
    overflow: hidden;
}

@media (max-width: 760px) {
    .app-container {
        flex-direction: column;
        gap: 10px;
    }
}
</style>
