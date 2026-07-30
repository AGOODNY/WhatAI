<template>
    <div class="layout">
        <MainSidebar />

        <div class="content">
            <router-view />
        </div>
    </div>
</template>

<script setup>
import MainSidebar from "../components/layout/MainSidebar.vue"
</script>

<style scoped>
.layout {
    width: 100%;
    min-width: 0;
    min-height: 100dvh;
    height: 100dvh;
    display: flex;
    gap: 16px;
    padding: 16px;
    overflow: hidden;
}

.content {
    flex: 1;
    min-width: 0;
    min-height: 0;
    display: flex;
    overflow: hidden;
}

@media (max-width: 760px) {
    .layout {
        flex-direction: column;
        gap: 10px;
        padding: 10px;
    }
}
</style>
