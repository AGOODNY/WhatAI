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

const emit = defineEmits([
    "send"
])

const text = ref("")

function send(){

    if(!text.value.trim()) return

    emit("send", text.value)

    text.value = ""
}
</script>

<style scoped>
.input-bar{
    height:70px;
    border-top:1px solid #ddd;

    display:flex;
    align-items:center;

    padding:0 20px;

    background:white;
}

input{
    flex:1;

    height:42px;

    border:1px solid #ccc;

    border-radius:8px;

    padding:0 12px;

    outline:none;
}

button{
    margin-left:12px;

    width:80px;
    height:42px;

    border:none;

    background:#5865f2;
    color:white;

    border-radius:8px;

    cursor:pointer;
}
</style>