<template>
    <div class="message-item">
        <img class="avatar" :src="avatarUrl" alt="avatar" />

        <div class="content">
            <div class="username">
                {{ displayName }}
            </div>

            <div class="bubble">
                {{ content }}
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue"
import { PERSONA_MAP } from "../../constants/personas"

const props = defineProps({
    role: String,
    persona: Object,
    content: String
})

const displayName = computed(() => {
    if (props.persona?.name) return props.persona.name
    return PERSONA_MAP[props.role]?.name || props.role
})

const avatarUrl = computed(() => {
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
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
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
