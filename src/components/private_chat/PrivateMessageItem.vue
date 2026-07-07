<template>

    <div
        class="message-wrapper"
        :class="{
            mine: isMine
        }"
    >

        <img
            :src="avatar"
            class="avatar"
        />

        <div class="message-content">

            <div class="nickname">
                {{ nickname }}
            </div>

            <div class="bubble">
                {{ message.content }}
            </div>

        </div>

    </div>

</template>

<script setup>
const props = defineProps({

    message: Object,

    isMine: Boolean,

    avatar: String,

    nickname: String,
})
</script>

<style scoped>
.message-wrapper {
    display: flex;
    margin-bottom: 18px;
}

.message-wrapper.mine {
    flex-direction: row-reverse;
}

.avatar {
    width: 42px;
    height: 42px;
    flex: 0 0 auto;
    border: 3px solid rgba(255, 255, 255, 0.82);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 8px 18px rgba(164, 109, 78, 0.12);
}

.message-content {
    max-width: min(62%, 620px);
    min-width: 0;
    margin: 0 12px;
}

.nickname {
    color: var(--color-muted);
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 5px;
    text-align: left;
}

.message-wrapper.mine .nickname {
    text-align: right;
}

.bubble {
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(249, 140, 83, 0.12);
    border-radius: 16px 16px 16px 6px;
    padding: 12px 14px;
    color: var(--color-text);
    line-height: 1.55;
    word-break: break-word;
    box-shadow: 0 8px 18px rgba(164, 109, 78, 0.08);
}

.message-wrapper.mine .bubble {
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.94), rgba(171, 215, 251, 0.55));
    border-color: rgba(249, 140, 83, 0.24);
    border-radius: 16px 16px 6px 16px;
}
</style>
