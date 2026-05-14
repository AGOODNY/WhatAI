<template>
    <div class="chat-window">

        <div class="header">

            <img
                :src="persona.avatar"
                class="header-avatar"
            />

            <div class="header-name">
                {{ persona.name }}
            </div>

        </div>

        <div
            class="messages"
            ref="messageContainer"
        >

            <PrivateMessageItem
                v-for="msg in messages"
                :key="msg.id"
                :message="msg"
                :isMine="msg.sender_type === 'user'"
                :avatar="getAvatar(msg)"
                :nickname="getNickname(msg)"
            />

        </div>

        <MessageInput
            @send="sendMessage"
        />

    </div>
</template>

<script setup>
import {
    ref,
    computed,
    onMounted,
    watch,
    nextTick
} from "vue"

import axios from "../../api/axios"

import {
    PERSONA_MAP
} from "../../constants/personas"

import PrivateMessageItem
from "./PrivateMessageItem.vue"

import MessageInput
from "./MessageInput.vue"

const props = defineProps({
    room: Object,
})

const messages = ref([])

const me = ref(null)

const messageContainer = ref(null)

const persona = computed(() => {

    return PERSONA_MAP[
        props.room.ai_role
    ]
})

async function fetchMe() {

    const res = await axios.get(
        "/api/users/me/"
    )

    me.value = res.data
}

async function fetchMessages() {

    const res = await axios.get(
        `/api/private-chat/rooms/${props.room.id}/messages/`
    )

    messages.value = res.data

    await nextTick()

    scrollToBottom()
}

async function sendMessage(content) {

    try {

        const localUserMsg = {
            id: Date.now(),
            sender_type: "user",
            content,
        }

        messages.value.push(
            localUserMsg
        )

        await nextTick()

        scrollToBottom()

        const res = await axios.post(
            `/api/private-chat/rooms/${props.room.id}/send/`,
            {
                content
            }
        )

        messages.value.pop()

        messages.value.push(
            res.data.user_message
        )

        messages.value.push(
            res.data.ai_message
        )

        await nextTick()

        scrollToBottom()

    } catch (err) {

        console.error(err)
    }
}

function scrollToBottom() {

    const el = messageContainer.value

    if (!el) return

    el.scrollTo({
        top: el.scrollHeight,
        behavior: "smooth",
    })
}

function getAvatar(msg) {

    if (msg.sender_type === "user") {

        return (
            me.value?.avatar_url
            || "/avatars/default.jpg"
        )
    }

    return persona.value.avatar
}

function getNickname(msg) {

    if (msg.sender_type === "user") {

        return (
            me.value?.nickname
            || "nickname"
        )
    }

    return persona.value.name
}

watch(
    () => props.room.id,
    async () => {

        await fetchMessages()
    }
)

onMounted(async () => {

    await fetchMe()

    await fetchMessages()
})
</script>

<style scoped>
.chat-window{
    flex:1;
    display:flex;
    flex-direction:column;
    height:100%;
}

.header{
    height:70px;
    background:white;
    border-bottom:1px solid #ddd;
    display:flex;
    align-items:center;
    padding:0 20px;
}

.header-avatar{
    width:42px;
    height:42px;
    border-radius:50%;
}

.header-name{
    margin-left:12px;
    font-size:18px;
    font-weight:bold;
}

.messages{
    flex:1;
    overflow-y:auto;
    padding:20px;
    background:#f5f5f5;
}
</style>