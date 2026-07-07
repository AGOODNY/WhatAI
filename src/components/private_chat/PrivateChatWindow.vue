<template>
    <div class="chat-window">

        <div class="header">

            <img
                :src="persona.avatar_url || persona.avatar"
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
    return props.room.persona || {
        name: props.room.ai_role,
        avatar_url: "/avatars/default.jpg",
    }
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

    return persona.value.avatar_url || persona.value.avatar || "/avatars/default.jpg"
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
.chat-window {
    flex: 1;
    min-width: 0;
    min-height: 0;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.header {
    min-height: 70px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(252, 206, 180, 0.45));
    border-bottom: 1px solid rgba(249, 140, 83, 0.18);
    display: flex;
    align-items: center;
    padding: 0 22px;
    flex: 0 0 auto;
}

.header-avatar {
    width: 46px;
    height: 46px;
    border: 3px solid rgba(255, 255, 255, 0.82);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 10px 22px rgba(164, 109, 78, 0.14);
}

.header-name {
    margin-left: 12px;
    color: #4c4038;
    font-size: 18px;
    font-weight: 900;
}

.messages {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 24px;
    background:
        linear-gradient(rgba(255, 255, 255, 0.35), rgba(255, 255, 255, 0.35)),
        radial-gradient(circle at 0 0, rgba(171, 215, 251, 0.22), transparent 18rem),
        radial-gradient(circle at 100% 100%, rgba(210, 224, 170, 0.18), transparent 20rem);
}
</style>
