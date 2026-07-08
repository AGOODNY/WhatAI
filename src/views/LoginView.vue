<template>
    <div class="login-page">
        <div class="login-shell">
            <section class="login-intro">
                <div class="brand-mark">CS</div>
                <h1>欢迎回来</h1>
                <p>登录 ChatSim，继续你的群聊模拟与角色对话。</p>
            </section>

            <form class="login-box" @submit.prevent="login">
                <div class="form-heading">
                    <span>账号登录</span>
                    <small>保持轻松，也保持可控</small>
                </div>

                <label class="field">
                    <span>账号</span>
                    <input
                        v-model="username"
                        autocomplete="username"
                        placeholder="请输入账号"
                    />
                </label>

                <label class="field">
                    <span>密码</span>
                    <input
                        v-model="password"
                        type="password"
                        autocomplete="current-password"
                        placeholder="请输入密码"
                    />
                </label>

                <button class="login-btn" type="submit">
                    登录
                </button>

                <button class="jump" type="button" @click="goRegister">
                    没有账号？去注册
                </button>
            </form>
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
.login-page {
    width: 100%;
    min-height: 100dvh;
    padding: 24px;
    display: grid;
    place-items: center;
    overflow: auto;
}

.login-shell {
    width: min(920px, 100%);
    min-height: 520px;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    gap: 18px;
    padding: 18px;
    border: 1px solid var(--color-border);
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.58);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.login-intro {
    min-width: 0;
    padding: 42px;
    border-radius: 22px;
    background:
        radial-gradient(circle at 20% 18%, rgba(252, 206, 180, 0.95), transparent 16rem),
        radial-gradient(circle at 80% 72%, rgba(171, 215, 251, 0.82), transparent 18rem),
        linear-gradient(135deg, rgba(249, 242, 239, 0.92), rgba(210, 224, 170, 0.5));
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.brand-mark {
    width: 58px;
    height: 58px;
    display: grid;
    place-items: center;
    border-radius: 18px;
    background: #ffffff;
    color: var(--color-primary);
    font-size: 20px;
    font-weight: 900;
    box-shadow: 0 14px 28px rgba(164, 109, 78, 0.14);
}

.login-intro h1 {
    margin: 28px 0 12px;
    color: #46382f;
    font-size: clamp(32px, 5vw, 52px);
    line-height: 1.05;
    letter-spacing: 0;
}

.login-intro p {
    max-width: 420px;
    margin: 0;
    color: #75685f;
    font-size: 16px;
    line-height: 1.8;
    font-weight: 700;
}

.login-box {
    min-width: 0;
    padding: 34px;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.86);
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 16px;
}

.form-heading {
    margin-bottom: 6px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.form-heading span {
    color: #4c4038;
    font-size: 24px;
    font-weight: 900;
}

.form-heading small {
    color: var(--color-muted);
    font-size: 13px;
    font-weight: 700;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: #5e5148;
    font-size: 13px;
    font-weight: 800;
}

.field input {
    width: 100%;
    min-height: 46px;
    padding: 12px 14px;
    border: 1px solid rgba(249, 140, 83, 0.24);
    border-radius: 14px;
    outline: none;
    background: rgba(249, 242, 239, 0.6);
    color: var(--color-text);
    transition:
        border-color 0.2s ease,
        background-color 0.2s ease,
        box-shadow 0.2s ease;
}

.field input:focus {
    border-color: rgba(249, 140, 83, 0.65);
    background: #ffffff;
    box-shadow: 0 0 0 4px rgba(249, 140, 83, 0.12);
}

.login-btn {
    min-height: 48px;
    margin-top: 6px;
    border-radius: 15px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: #ffffff;
    cursor: pointer;
    font-size: 15px;
    font-weight: 900;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.24);
    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease,
        filter 0.2s ease;
}

.login-btn:hover {
    filter: saturate(1.06);
    box-shadow: 0 18px 32px rgba(249, 140, 83, 0.32);
    transform: translateY(-1px);
}

.jump {
    align-self: center;
    padding: 8px 10px;
    border-radius: 999px;
    background: transparent;
    color: #6b7d35;
    cursor: pointer;
    font-size: 13px;
    font-weight: 800;
}

.jump:hover {
    background: rgba(210, 224, 170, 0.38);
}

@media (max-width: 760px) {
    .login-page {
        padding: 12px;
        align-items: start;
    }

    .login-shell {
        min-height: auto;
        grid-template-columns: 1fr;
        padding: 12px;
        border-radius: 22px;
    }

    .login-intro {
        padding: 28px;
        border-radius: 18px;
    }

    .login-box {
        padding: 24px;
        border-radius: 18px;
    }
}
</style>
