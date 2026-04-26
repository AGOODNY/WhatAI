<!-- 文件：src/App.vue -->
<template>
  <div class="app-container">

    <!-- 左侧聊天列表 -->
    <ChatSidebar
      :currentRoomId="currentRoomId"
      @selectRoom="selectRoom"
      @createRoom="goToCreate"
    />

    <!-- 右侧聊天窗口（已替换） -->
    <ChatWindow
      :roomId="currentRoomId"
      :roomName="currentRoomName"
    />

  </div>
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