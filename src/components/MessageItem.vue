<!-- 文件：src/components/MessageItem.vue -->
<template>
    <div class="message-item">

        <!-- 头像 -->
        <div class="avatar" :style="{ backgroundColor: avatarColor }">
            {{ role }}
        </div>

        <!-- 内容区 -->
        <div class="content">
            <div class="username">
                {{ role }}
            </div>

            <div class="bubble">
                {{ content }}
            </div>
        </div>

    </div>
</template>

<script setup>
import { computed } from "vue"

/**
 * 接收消息数据
 */
const props = defineProps({
    role: String,
    content: String
})

/**
 * 根据角色生成头像颜色
 */
const avatarColor = computed(() => {
    const map = {
        A: "#ff6b6b",
        B: "#4dabf7",
        C: "#51cf66",
        D: "#868e96"
    }
    return map[props.role] || "#999"
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
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    font-weight: bold;
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