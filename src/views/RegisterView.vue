<template>
    <div class="register-page">

        <div class="register-box">

            <h1>注册</h1>

            <input
                v-model="username"
                placeholder="账号"
            />

            <input
                v-model="password"
                type="password"
                placeholder="密码"
            />

            <button @click="register">
                注册
            </button>

        </div>

    </div>
</template>

<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"

import axios from "@/api/axios"

const router = useRouter()

const username = ref("")
const password = ref("")

async function register() {

    try {

        await axios.post(
            "/api/users/register/",
            {
                username: username.value,
                password: password.value
            }
        )

        alert("注册成功")

        router.push("/login")

    } catch (err) {

        alert("注册失败")
    }
}
</script>

<style scoped>
.register-page{
    width:100vw;
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    background:#f5f5f5;
}

.register-box{
    width:320px;
    padding:30px;
    background:white;
    border-radius:12px;
    display:flex;
    flex-direction:column;
    gap:15px;
}
</style>