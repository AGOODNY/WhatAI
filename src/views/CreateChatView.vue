<template>
    <div class="create-page">
        <section class="main">
            <h2>创建群聊</h2>

            <div class="form-item">
                <label>聊天名称</label>
                <input v-model="name" placeholder="例如：小说讨论会" />
            </div>

            <div class="form-item">
                <label>聊天情景</label>
                <textarea v-model="scenario" placeholder="例如：几位角色正在讨论一部科幻小说" />
            </div>

            <div class="section-title">
                选择 2-4 个 AI 人格
            </div>

            <div class="persona-grid">
                <div
                    v-for="persona in personas"
                    :key="persona.id"
                    class="persona-card"
                    :class="{ selected: selectedIds.includes(persona.id) }"
                    @click="togglePersona(persona)"
                >
                    <img :src="persona.avatar_url" class="avatar" />
                    <div class="name">{{ persona.name }}</div>
                    <div class="tag">{{ persona.is_builtin ? "内置" : "我的" }}</div>
                </div>
            </div>

            <div class="actions">
                <button @click="handleCreate">创建</button>
                <button class="cancel" @click="goBack">取消</button>
            </div>
        </section>

        <aside class="quick-create">
            <h3>快速新建人格</h3>
            <PersonaForm
                submitText="添加到人格库"
                :showCancel="false"
                @submit="createPersona"
            />
        </aside>
    </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import axios from "@/api/axios"
import { useRouter } from "vue-router"
import PersonaForm from "../components/personas/PersonaForm.vue"

const router = useRouter()

const name = ref("")
const scenario = ref("")
const personas = ref([])
const selectedIds = ref([])

async function fetchPersonas() {
    const res = await axios.get("/api/personas/")
    personas.value = res.data
}

function togglePersona(persona) {
    const index = selectedIds.value.indexOf(persona.id)

    if (index >= 0) {
        selectedIds.value.splice(index, 1)
        return
    }

    if (selectedIds.value.length >= 4) {
        alert("群聊最多选择 4 个 AI 人格")
        return
    }

    selectedIds.value.push(persona.id)
}

async function createPersona(payload) {
    const res = await axios.post("/api/personas/", payload)
    personas.value.push(res.data)
    if (selectedIds.value.length < 4) {
        selectedIds.value.push(res.data.id)
    }
}

async function handleCreate() {
    if (!name.value.trim() || !scenario.value.trim()) {
        alert("请填写聊天名称和情景")
        return
    }

    if (selectedIds.value.length < 2 || selectedIds.value.length > 4) {
        alert("请选择 2-4 个 AI 人格")
        return
    }

    try {
        await axios.post(
            "/api/chat/rooms/create/",
            {
                name: name.value,
                scenario: scenario.value,
                persona_ids: selectedIds.value,
            }
        )

        router.push("/")

    } catch (err) {
        console.error(err)
        alert("创建失败")
    }
}

function goBack() {
    router.push("/")
}

onMounted(fetchPersonas)
</script>

<style scoped>
.create-page {
    height: 100%;
    display: flex;
    background: #f5f7fb;
}

.main {
    flex: 1;
    padding: 32px;
    overflow-y: auto;
}

.quick-create {
    width: 360px;
    padding: 32px;
    background: white;
    border-left: 1px solid #e5e7eb;
    overflow-y: auto;
}

h2,
h3 {
    margin-top: 0;
}

.form-item {
    margin-bottom: 18px;
}

label,
.section-title {
    display: block;
    margin-bottom: 8px;
    font-weight: 700;
}

input,
textarea {
    width: 100%;
    box-sizing: border-box;
    border: 1px solid #d8dee8;
    border-radius: 8px;
    padding: 11px 12px;
    font-size: 14px;
}

textarea {
    min-height: 110px;
    resize: vertical;
}

.persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 14px;
}

.persona-card {
    background: white;
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 14px;
    cursor: pointer;
    text-align: center;
}

.persona-card.selected {
    border-color: #5865f2;
    background: #eef2ff;
}

.avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    object-fit: cover;
}

.name {
    margin-top: 10px;
    font-weight: 700;
}

.tag {
    margin-top: 4px;
    font-size: 12px;
    color: #5865f2;
}

.actions {
    margin-top: 24px;
    display: flex;
    gap: 10px;
}

button {
    border: 0;
    border-radius: 8px;
    padding: 10px 18px;
    background: #5865f2;
    color: white;
    cursor: pointer;
}

.cancel {
    background: #d1d5db;
    color: #111827;
}
</style>
