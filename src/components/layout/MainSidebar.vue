<template>
    <div class="main-sidebar">
        <button
            v-for="item in navItems"
            :key="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
            type="button"
            @click="go(item.path)"
        >
            {{ item.label }}
        </button>
    </div>
</template>

<script setup>
import { useRoute, useRouter } from "vue-router"

const router = useRouter()
const route = useRoute()

const navItems = [
    { label: "群聊", path: "/group" },
    { label: "私聊", path: "/private" },
    { label: "人格库", path: "/personas" },
    { label: "个人中心", path: "/profile" },
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
    min-height: 44px;
    padding: 12px 14px;
    border-radius: 14px;
    background: transparent;
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
        min-width: 72px;
        min-height: 40px;
        padding: 10px 12px;
        white-space: nowrap;
    }
}
</style>
