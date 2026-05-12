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
.layout{
    width:100vw;
    height:100vh;
    display:flex;
}

.content{
    flex:1;
}
</style>