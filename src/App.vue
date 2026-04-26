<!-- 文件：src/App.vue -->
<template>
  <router-view />
</template>

<script setup>
import { ref, computed } from "vue"
import ChatSidebar from "./components/ChatSidebar.vue"
import ChatWindow from "./components/ChatWindow.vue"

/**
 * 当前选中的房间ID
 */
const currentRoomId = ref(null)

/**
 * 当前房间名称（临时实现）
 */
const currentRoomName = computed(() => {
  return currentRoomId.value ? `房间 ${currentRoomId.value}` : "未选择"
})

/**
 * 切换聊天
 */
function selectRoom(id) {
  currentRoomId.value = id
  console.log("当前房间:", id)
}

/**
 * 新建聊天
 */
function goToCreate() {
  alert("跳转到创建聊天页面（下一步实现）")
}
</script>

<style scoped>
/* 整体布局 */
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  background: #f5f5f5;
}
</style>