<template>

    <div class="main-sidebar">

        <div
            class="nav-item"
            @click="goHome"
        >
            群聊
        </div>

        <div
            class="nav-item"
            @click="goPrivate"
        >
            私聊
        </div>

        <div
            class="nav-item"
            @click="goProfile"
        >
            个人中心
        </div>

    </div>

</template>

<script setup>
import { useRouter } from "vue-router"

const router = useRouter()

function goHome() {
    router.push("/")
}

function goPrivate() {
    router.push("/private")
}

function goProfile() {
    router.push("/profile")
}
</script>

<style scoped>
.main-sidebar{
    width:120px;
    background:#202225;
    color:white;
    display:flex;
    flex-direction:column;
}

.nav-item{
    padding:20px;
    cursor:pointer;
}

.nav-item:hover{
    background:#2f3136;
}
</style>