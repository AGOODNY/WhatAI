<template>
    <div class="create-container">
        <h2>创建新聊天</h2>

        <div class="form-item">
            <label>聊天名称</label>
            <input v-model="name" placeholder="例如：小说讨论" />
        </div>

        <div class="form-item">
            <label>聊天情景</label>
            <textarea v-model="scenario" placeholder="例如：角色ABCD正在讨论写一本科幻小说" />
        </div>

        <div class="actions">
            <button @click="handleCreate">创建</button>
            <button class="cancel" @click="goBack">取消</button>
        </div>
    </div>
</template>

<script setup>
import { ref } from "vue"
import axios from "axios"
import { useRouter } from "vue-router"

const router = useRouter()

const name = ref("")
const scenario = ref("")

async function handleCreate() {
    if (!name.value || !scenario.value) {
        alert("请填写完整")
        return
    }

    try {
        const res = await axios.post(
            "/api/chat/rooms/create/",
            {
                name: name.value,
                scenario: scenario.value
            }
        )

        console.log("创建成功:", res.data)

        // 创建成功后跳回首页
        router.push("/")

    } catch (err) {
        console.error("创建失败:", err)
        alert("创建失败")
    }
}

function goBack() {
    router.push("/")
}
</script>

<style scoped>
.create-container {
    max-width: 500px;
    margin: 80px auto;
    background: white;
    padding: 30px;
    border-radius: 10px;
}

.form-item {
    margin-bottom: 20px;
}

input,
textarea {
    width: 100%;
    padding: 10px;
    margin-top: 5px;
    border: 1px solid #ddd;
    border-radius: 6px;
}

textarea {
    height: 100px;
}

.actions {
    display: flex;
    gap: 10px;
}

button {
    padding: 10px 20px;
    cursor: pointer;
}

.cancel {
    background: #ccc;
}
</style>