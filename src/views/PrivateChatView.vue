<template>
    <div class="private-chat-page">

        <PrivateRoomSidebar
            :rooms="rooms"
            :currentRoomId="currentRoom?.id"
            @select="enterRoom"
            @new-chat="backToSelect"
        />

        <div class="content">

            <CharacterSelect
                v-if="!currentRoom"
                @room-created="handleCreated"
            />

            <PrivateChatWindow
                v-else
                :room="currentRoom"
            />

        </div>

    </div>
</template>

<script setup>
import {
    ref,
    onMounted
} from "vue"

import axios from "../api/axios"

import CharacterSelect
from "../components/private_chat/CharacterSelect.vue"

import PrivateChatWindow
from "../components/private_chat/PrivateChatWindow.vue"

import PrivateRoomSidebar
from "../components/private_chat/PrivateRoomSidebar.vue"

const currentRoom = ref(null)

const rooms = ref([])

async function fetchRooms() {

    const res = await axios.get(
        "/api/private-chat/rooms/"
    )

    rooms.value = res.data
}

function enterRoom(room) {

    currentRoom.value = room
}

function backToSelect() {

    currentRoom.value = null
}

async function handleCreated(room) {

    await fetchRooms()

    currentRoom.value = room
}

onMounted(fetchRooms)
</script>

<style scoped>
.private-chat-page {
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: flex;
    gap: 16px;
    overflow: hidden;
}

.content {
    flex: 1;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: flex;
    overflow: hidden;
}

@media (max-width: 760px) {
    .private-chat-page {
        flex-direction: column;
        gap: 10px;
    }
}
</style>
