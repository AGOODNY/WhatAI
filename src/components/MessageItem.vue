<!-- 文件：src/components/MessageItem.vue -->
<template>
    <div class="message-item">

        <!-- 头像 -->
        <img class="avatar" :src="avatarUrl" alt="avatar" />

        <!-- 内容区 -->
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
import { PERSONA_MAP } from "../constants/personas"

/**
 * 接收消息数据
 */
const props = defineProps({
    role: String,
    content: String
})

const displayName = computed(() => {
    return PERSONA_MAP[props.role]?.name || props.role
})

/**
 * 头像
 */
const avatarUrl = computed(() => {
    return `/avatars/${props.role}.jpg`
})
</script>

<style scoped>
.message-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 15px;
}

/* 头像 */
.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-right: 10px;
    object-fit: cover;
}

/* 内容 */
.content {
    max-width: 70%;
}

/* 用户名 */
.username {
    font-size: 12px;
    color: #888;
    margin-bottom: 5px;
}

/* 气泡 */
.bubble {
    background: #ffffff;
    border-radius: 10px;
    padding: 10px 15px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    word-break: break-word;
}
</style>