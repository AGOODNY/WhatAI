<template>
    <div
        class="message-item"
        :class="{ mine: isMine }"
        @contextmenu="handleContextMenu"
    >
        <img class="avatar" :src="avatarUrl" alt="avatar" />

        <div class="content">
            <div class="username">
                {{ displayName }}
            </div>

            <div class="bubble">
                <button
                    v-if="replyTo"
                    type="button"
                    class="quoted-message"
                    @click="emit('jumpToMessage', replyTo.id)"
                >
                    <strong>{{ replyTo.display_name }}</strong>
                    <span>{{ replyTo.content }}</span>
                </button>
                <div class="message-text">{{ content }}</div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue"
import { PERSONA_MAP } from "../../constants/personas"

const emit = defineEmits(["openQuoteMenu", "jumpToMessage"])

const props = defineProps({
    role: String,
    persona: Object,
    content: String,
    isMine: Boolean,
    user: Object,
    replyTo: Object,
    canQuote: Boolean,
})

function handleContextMenu(event) {
    if (!props.canQuote) return
    event.preventDefault()
    emit("openQuoteMenu", event)
}

const displayName = computed(() => {
    if (props.isMine) return props.user?.nickname || props.user?.username || "我"
    if (props.persona?.name) return props.persona.name
    return PERSONA_MAP[props.role]?.name || props.role
})

const avatarUrl = computed(() => {
    if (props.isMine) return props.user?.avatar_url || "/avatars/default.jpg"
    if (props.persona?.avatar_url) return props.persona.avatar_url
    return `/avatars/${props.role}.jpg`
})
</script>

<style scoped>
.message-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 18px;
    min-width: 0;
}

.message-item.mine {
    flex-direction: row-reverse;
}

.message-item.mine .content {
    align-items: flex-end;
}

.message-item.mine .username {
    padding-right: 2px;
    text-align: right;
}

.message-item.mine .bubble {
    border-color: rgba(249, 140, 83, 0.38);
    border-radius: 18px 18px 6px 18px;
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.86), rgba(255, 239, 225, 0.94));
}

.avatar {
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(255, 255, 255, 0.95);
    box-shadow: 0 8px 18px rgba(164, 109, 78, 0.14);
}

.content {
    max-width: min(72%, 760px);
    min-width: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.username {
    max-width: 100%;
    margin-bottom: 6px;
    padding-left: 2px;
    color: var(--color-muted);
    font-size: 12px;
    font-weight: 800;
    line-height: 1;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.bubble {
    max-width: 100%;
    padding: 12px 15px;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(252, 206, 180, 0.55);
    border-radius: 18px 18px 18px 6px;
    box-shadow: 0 8px 20px rgba(164, 109, 78, 0.08);
    color: #4f463f;
    font-size: 15px;
    line-height: 1.6;
    text-align: left;
    overflow-wrap: anywhere;
    word-break: break-word;
}

.message-text {
    white-space: pre-wrap;
}

.quoted-message {
    width: 100%;
    min-width: 0;
    margin: -3px 0 9px;
    padding: 7px 10px;
    border: 0;
    border-left: 3px solid rgba(249, 140, 83, 0.72);
    border-radius: 8px;
    background: rgba(93, 79, 68, 0.07);
    color: inherit;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    gap: 2px;
    text-align: left;
}

.quoted-message strong,
.quoted-message span {
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.quoted-message strong {
    color: #b86743;
    font-size: 12px;
}

.quoted-message span {
    color: #75685f;
    font-size: 12px;
}

@media (max-width: 760px) {
    .message-item {
        gap: 10px;
        margin-bottom: 16px;
    }

    .avatar {
        width: 38px;
        height: 38px;
        flex-basis: 38px;
    }

    .content {
        max-width: calc(100% - 48px);
    }

    .bubble {
        padding: 10px 12px;
        font-size: 14px;
        border-radius: 16px 16px 16px 6px;
    }
}
</style>
