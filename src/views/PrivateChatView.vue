<template>

    <div class="private-chat-page">

        <CharacterSelect
            v-if="!currentRoom"
            @room-created="enterRoom"
        />

        <PrivateChatWindow
            v-else
            :room="currentRoom"
        />

    </div>

</template>

<script setup>
import { ref } from "vue"

import CharacterSelect from "../components/private_chat/CharacterSelect.vue"

import PrivateChatWindow from "../components/private_chat/PrivateChatWindow.vue"

const currentRoom = ref(null)

function enterRoom(room){

    currentRoom.value = room
}
</script>

<style scoped>
.private-chat-page{
    width:100%;
    height:100%;
}
</style>