<template>
    <div class="main-sidebar">
        <div class="nav-item" @click="goHome">
            群聊
        </div>

        <div class="nav-item" @click="goPrivate">
            私聊
        </div>

        <div class="nav-item" @click="goPersonas">
            人格库
        </div>

        <div class="nav-item" @click="goProfile">
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

function goPersonas() {
    router.push("/personas")
}

function goProfile() {
    router.push("/profile")
}
</script>

<style scoped>
.main-sidebar {
    width: 132px;
    flex: 0 0 132px;
    min-height: 0;
    padding: 14px 10px;
    background: rgba(255, 255, 255, 0.72);
    color: var(--color-text);
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-card);
    backdrop-filter: blur(18px);
}

.nav-item {
    min-height: 44px;
    padding: 12px 14px;
    border-radius: 14px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 700;
    line-height: 1.35;
    text-align: center;
    color: #6b5b50;
    transition:
        background-color 0.2s ease,
        color 0.2s ease,
        transform 0.2s ease,
        box-shadow 0.2s ease;
}

.nav-item:hover {
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.75), rgba(171, 215, 251, 0.45));
    color: #3d332d;
    box-shadow: 0 8px 20px rgba(249, 140, 83, 0.14);
    transform: translateY(-1px);
}

@media (max-width: 760px) {
    .main-sidebar {
        width: 100%;
        flex: 0 0 auto;
        min-height: auto;
        flex-direction: row;
        overflow-x: auto;
        padding: 8px;
        border-radius: 18px;
    }

    .nav-item {
        flex: 1 0 max-content;
        min-width: 72px;
        min-height: 40px;
        padding: 10px 12px;
        white-space: nowrap;
    }
}
</style>
