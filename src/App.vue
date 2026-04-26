<!-- 文件：src/App.vue -->
<template>
  <div class="app-container">
    <!-- 左侧（改为组件） -->
    <ChatSidebar
      :currentRoomId="currentRoomId"
      @selectRoom="selectRoom"
      @createRoom="goToCreate"
    />

    <!-- 右侧聊天窗口 -->
    <div class="chat-area">
      <div class="chat-header">
        当前聊天：{{ currentRoomName }}
      </div>

      <div class="chat-content">
        <p v-if="!currentRoomId">请选择一个聊天</p>
        <p v-else>这里将显示聊天内容（下一步实现）</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import ChatSidebar from "./components/ChatSidebar.vue"

/**
 * 当前选中的房间ID（核心状态）
 */
const currentRoomId = ref(null)

/**
 * 计算当前房间名称
 * ⚠️ 这里暂时保留简单版本（后面会从Sidebar传数据或用store优化）
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
 * 新建聊天（后面接路由）
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

/* 右侧聊天区 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 顶部 */
.chat-header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #ddd;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-weight: bold;
}

/* 内容区 */
.chat-content {
  flex: 1;
  padding: 20px;
}
</style>