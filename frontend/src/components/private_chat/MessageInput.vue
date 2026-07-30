<template>
    <div class="input-bar">
        <input
            v-model="text"
            @keyup.enter="send"
            placeholder="输入消息..."
        />

        <button @click="send">
            发送
        </button>
    </div>
</template>

<script setup>
import { ref } from "vue"

const emit = defineEmits(["send"])

const text = ref("")

function send() {
    if (!text.value.trim()) return

    emit("send", text.value)
    text.value = ""
}
</script>

<style scoped>
.input-bar {
    flex: 0 0 auto;
    min-height: 74px;
    border-top: 1px solid rgba(249, 140, 83, 0.16);
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    background: rgba(255, 255, 255, 0.78);
}

input {
    flex: 1;
    min-width: 0;
    height: 46px;
    border: 1px solid rgba(249, 140, 83, 0.22);
    border-radius: 16px;
    padding: 0 14px;
    background: rgba(249, 242, 239, 0.72);
    color: var(--color-text);
    outline: none;
}

input:focus {
    border-color: rgba(249, 140, 83, 0.55);
    background: #fff;
    box-shadow: 0 0 0 4px rgba(252, 206, 180, 0.3);
}

button {
    height: 46px;
    min-width: 82px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: white;
    cursor: pointer;
    font-weight: 900;
    box-shadow: 0 12px 24px rgba(249, 140, 83, 0.22);
}
</style>
