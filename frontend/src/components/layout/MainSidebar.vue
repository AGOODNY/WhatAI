<template>
    <nav class="main-sidebar" aria-label="主导航">
        <button
            v-for="item in navItems"
            :key="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            type="button"
            @click="go(item.path)"
        >
            <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
        </button>
    </nav>
</template>

<script setup>
import { useRoute, useRouter } from "vue-router"

const router = useRouter()
const route = useRoute()

const navItems = [
    { label: "群聊", icon: "聊", path: "/group" },
    { label: "私聊", icon: "私", path: "/private" },
    { label: "人格库", icon: "人", path: "/personas" },
    { label: "游玩", icon: "玩", path: "/play" },
    { label: "个人中心", icon: "我", path: "/profile" },
]

function go(path) {
    router.push(path)
}

function isActive(path) {
    if (path === "/group") {
        return route.path === "/" || route.path === "/group" || route.path === "/create"
    }
    return route.path === path || route.path.startsWith(`${path}/`)
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
    min-height: 52px;
    padding: 9px 10px;
    border-radius: 14px;
    background: transparent;
    cursor: pointer;
    font-size: 14px;
    font-weight: 700;
    color: #6b5b50;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.nav-icon {
    width: 25px;
    height: 25px;
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.62);
    display: grid;
    place-items: center;
    font-size: 12px;
    font-weight: 900;
}

.nav-item:hover,
.nav-item.active {
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.75), rgba(171, 215, 251, 0.45));
    color: #3d332d;
    box-shadow: 0 8px 20px rgba(249, 140, 83, 0.14);
    transform: translateY(-1px);
}

.nav-item.active {
    border: 1px solid rgba(249, 140, 83, 0.28);
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
        min-width: 74px;
        min-height: 42px;
        padding: 8px 10px;
        white-space: nowrap;
    }
}
</style>
