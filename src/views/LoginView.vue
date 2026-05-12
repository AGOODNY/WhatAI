<template>
    <div class="login-page">

        <div class="login-box">

            <h1>登录</h1>

            <input
                v-model="username"
                placeholder="账号"
            />

            <input
                v-model="password"
                type="password"
                placeholder="密码"
            />

            <button @click="login">
                登录
            </button>

            <div class="jump" @click="goRegister">
                没有账号？去注册
            </div>

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

async function login() {

    try {

        const res = await axios.post(
            "/api/users/login/",
            {
                username: username.value,
                password: password.value
            }
        )

        localStorage.setItem(
            "token",
            res.data.access
        )

        router.push("/")

    } catch (err) {

        alert("登录失败")
    }
}

function goRegister() {
    router.push("/register")
}
</script>

<style scoped>
.login-page{
    width:100vw;
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    background:#f5f5f5;
}

.login-box{
    width:320px;
    padding:30px;
    background:white;
    border-radius:12px;
    display:flex;
    flex-direction:column;
    gap:15px;
}

input{
    padding:12px;
}

button{
    padding:12px;
    cursor:pointer;
}

.jump{
    color:blue;
    cursor:pointer;
}
</style>