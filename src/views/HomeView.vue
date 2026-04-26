<template>
    <div class="app-container">

        <ChatSidebar :currentRoomId="currentRoomId" @selectRoom="selectRoom" @createRoom="goToCreate" />

        <ChatWindow :roomId="currentRoomId" :roomName="currentRoomName" />

    </div>
</template>

<script setup>
import { ref, computed } from "vue"
import { useRouter } from "vue-router"

import ChatSidebar from "../components/ChatSidebar.vue"
import ChatWindow from "../components/ChatWindow.vue"

const router = useRouter()

const currentRoomId = ref(null)
const rooms = ref([]) // 可选：后续可从store统一管理

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
    width: 100vw;
    height: 100vh;
    display: flex;
}
</style>