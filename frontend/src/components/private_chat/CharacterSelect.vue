<template>
    <div class="select-page">
        <section class="personas-panel">
            <div class="panel-header">
                <div>
                    <p>Private chat</p>
                    <h2>选择私聊人格</h2>
                </div>
                <button @click="showCreate = !showCreate">
                    {{ showCreate ? "收起创建" : "新建人格" }}
                </button>
            </div>

            <div class="persona-grid">
                <button
                    v-for="persona in personas"
                    :key="persona.id"
                    class="persona-card"
                    @click="selectCharacter(persona.id)"
                >
                    <img :src="persona.avatar_url" class="avatar" />
                    <span class="name">{{ persona.name }}</span>
                    <span class="tag">{{ persona.is_builtin ? "内置" : "我的" }}</span>
                    <span class="desc">{{ persona.description || "点击开始一段新的私聊" }}</span>
                </button>
            </div>
        </section>

        <aside v-if="showCreate" class="creator">
            <div class="creator-title">
                <p>New persona</p>
                <h3>创建新人格</h3>
            </div>
            <PersonaForm
                submitText="创建并私聊"
                :showCancel="false"
                @submit="createAndChat"
            />
        </aside>
    </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import axios from "../../api/axios"
import PersonaForm from "../personas/PersonaForm.vue"

const emit = defineEmits(["room-created"])

const personas = ref([])
const showCreate = ref(false)

async function fetchPersonas() {
    const res = await axios.get("/api/personas/")
    personas.value = res.data
}

async function selectCharacter(persona_id) {
    try {
        const res = await axios.post(
            "/api/private-chat/rooms/create/",
            { persona_id }
        )

        emit("room-created", res.data)
    } catch (err) {
        console.error(err)
        alert("创建私聊失败")
    }
}

async function createAndChat(payload) {
    const res = await axios.post(
        "/api/personas/",
        payload,
        {
            headers: {
                "Content-Type": "multipart/form-data"
            }
        }
    )
    personas.value.push(res.data)
    await selectCharacter(res.data.id)
}

onMounted(fetchPersonas)
</script>

<style scoped>
.select-page {
    flex: 1;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: flex;
    gap: 16px;
}

.personas-panel,
.creator {
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.personas-panel {
    flex: 1;
    min-width: 0;
    padding: 24px;
    overflow-y: auto;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 18px;
    margin-bottom: 20px;
}

p {
    margin: 0 0 6px;
    color: var(--color-muted);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0;
    text-transform: uppercase;
}

h2,
h3 {
    margin: 0;
    color: #4c4038;
}

.panel-header button {
    flex: 0 0 auto;
    border-radius: 16px;
    padding: 12px 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: #fff;
    cursor: pointer;
    font-weight: 800;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.22);
}

.persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 14px;
}

.persona-card {
    min-height: 238px;
    padding: 18px;
    border: 1px solid rgba(171, 215, 251, 0.34);
    border-radius: 18px;
    background: rgba(249, 242, 239, 0.76);
    color: var(--color-text);
    cursor: pointer;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    box-shadow: 0 10px 24px rgba(164, 109, 78, 0.07);
    transition:
        transform 0.2s ease,
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        background-color 0.2s ease;
}

.persona-card:hover {
    transform: translateY(-2px);
    border-color: rgba(249, 140, 83, 0.45);
    background: #fffaf7;
    box-shadow: 0 16px 28px rgba(249, 140, 83, 0.14);
}

.avatar {
    width: 84px;
    height: 84px;
    border: 4px solid rgba(255, 255, 255, 0.8);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 10px 22px rgba(164, 109, 78, 0.14);
}

.name {
    margin-top: 14px;
    font-size: 17px;
    font-weight: 900;
}

.tag {
    margin-top: 7px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(171, 215, 251, 0.45);
    color: #467399;
    font-size: 12px;
    font-weight: 800;
}

.desc {
    width: 100%;
    margin-top: 12px;
    color: var(--color-muted);
    font-size: 13px;
    line-height: 1.5;
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.creator {
    width: min(380px, 36vw);
    min-width: 320px;
    padding: 24px;
    overflow-y: auto;
}

.creator-title {
    margin-bottom: 18px;
}

@media (max-width: 920px) {
    .select-page {
        flex-direction: column;
    }

    .creator {
        width: 100%;
        min-width: 0;
    }
}
</style>
