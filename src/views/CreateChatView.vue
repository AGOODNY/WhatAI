<template>
    <div class="create-page">
        <section class="personas-panel">
            <div class="panel-header">
                <div>
                    <p>Group chat</p>
                    <h2>创建群聊</h2>
                </div>
                <button class="toggle-create-btn" type="button" @click="showCreate = !showCreate">
                    {{ showCreate ? "收起创建" : "新建人格" }}
                </button>
            </div>

            <div class="setup-panel">
                <label class="form-item">
                    <span>聊天名称</span>
                    <input v-model="name" placeholder="例如：小说讨论会" />
                </label>

                <label class="form-item">
                    <span>聊天情景</span>
                    <textarea v-model="scenario" placeholder="例如：几位角色正在讨论一部科幻小说" />
                </label>

                <div class="setup-actions">
                    <div class="button-row">
                        <button class="primary-btn" type="button" @click="handleCreate">
                            创建群聊
                        </button>
                        <button class="ghost-btn" type="button" @click="goBack">
                            取消
                        </button>
                    </div>
                </div>
            </div>

            <div class="section-title">
                <p>Personas</p>
                <div class="section-title-row">
                    <h3>选择 2-4 个人格</h3>
                    <span class="count-pill">已选 {{ selectedIds.length }}/4</span>
                </div>
            </div>

            <div class="persona-grid">
                <button
                    v-for="persona in personas"
                    :key="persona.id"
                    type="button"
                    class="persona-card"
                    :class="{ selected: selectedIds.includes(persona.id) }"
                    @click="togglePersona(persona)"
                >
                    <img :src="persona.avatar_url" class="avatar" />
                    <span class="name">{{ persona.name }}</span>
                    <span class="tag">{{ persona.is_builtin ? "内置" : "我的" }}</span>
                    <span class="desc">{{ persona.description || "适合加入新的群聊" }}</span>
                </button>
            </div>
        </section>

        <aside v-if="showCreate" class="creator">
            <div class="creator-title">
                <p>New persona</p>
                <h3>快速新建人格</h3>
            </div>
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
const showCreate = ref(false)

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

.toggle-create-btn,
.primary-btn,
.ghost-btn {
    flex: 0 0 auto;
    border: 0;
    appearance: none;
    -webkit-appearance: none;
    border-radius: 16px;
    padding: 12px 16px;
    cursor: pointer;
    font-weight: 900;
}

.toggle-create-btn,
.primary-btn {
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: #fff;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.22);
}

.toggle-create-btn:hover,
.primary-btn:hover {
    filter: saturate(1.05);
    box-shadow: 0 16px 30px rgba(249, 140, 83, 0.3);
    transform: translateY(-1px);
}

.setup-panel {
    margin-bottom: 20px;
    padding: 16px;
    border: 1px solid rgba(171, 215, 251, 0.34);
    border-radius: 18px;
    background: rgba(249, 242, 239, 0.76);
    box-shadow: 0 10px 24px rgba(164, 109, 78, 0.07);
    display: grid;
    gap: 14px;
}

.form-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.form-item span {
    color: #6f625a;
    font-size: 13px;
    font-weight: 800;
}

input,
textarea {
    width: 100%;
    min-width: 0;
    border: 1px solid rgba(249, 140, 83, 0.2);
    border-radius: 16px;
    padding: 12px 14px;
    background: rgba(255, 255, 255, 0.84);
    color: var(--color-text);
    outline: none;
    transition:
        border-color 0.2s ease,
        box-shadow 0.2s ease,
        background-color 0.2s ease;
}

input:focus,
textarea:focus {
    border-color: rgba(249, 140, 83, 0.55);
    background: #fff;
    box-shadow: 0 0 0 4px rgba(252, 206, 180, 0.34);
}

textarea {
    min-height: 92px;
    resize: vertical;
}

.setup-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.count-pill {
    flex: 0 0 auto;
    padding: 5px 12px;
    border-radius: 999px;
    background: rgba(171, 215, 251, 0.45);
    color: #467399;
    font-size: 13px;
    font-weight: 900;
}

.button-row {
    display: flex;
    gap: 10px;
}

.ghost-btn {
    border-radius: 16px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.74);
    color: var(--color-text);
}

.section-title {
    margin-bottom: 14px;
}

.section-title-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
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

.persona-card.selected {
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.95), rgba(171, 215, 251, 0.58));
    border-color: rgba(249, 140, 83, 0.58);
    box-shadow: 0 16px 30px rgba(249, 140, 83, 0.18);
}

.avatar {
    width: 84px;
    height: 84px;
    border: 4px solid rgba(255, 255, 255, 0.82);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 10px 22px rgba(164, 109, 78, 0.14);
}

.name {
    width: 100%;
    margin-top: 14px;
    overflow: hidden;
    color: #4c4038;
    font-size: 17px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
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
    .create-page {
        flex-direction: column;
    }

    .creator {
        width: 100%;
        min-width: 0;
    }
}

@media (max-width: 560px) {
    .panel-header,
    .setup-actions,
    .button-row {
        flex-direction: column;
        align-items: stretch;
    }

    .panel-header button,
    .toggle-create-btn,
    .primary-btn,
    .ghost-btn {
        width: 100%;
    }
}
</style>
