<template>
    <div class="persona-page">
        <section class="library">
            <div class="header">
                <div>
                    <p>Persona library</p>
                    <h2>人格库</h2>
                </div>
                <button @click="startCreate">新建人格</button>
            </div>

            <div class="grid">
                <article
                    v-for="persona in personas"
                    :key="persona.id"
                    class="persona-card"
                >
                    <div class="topline">
                        <img :src="persona.avatar_url" class="avatar" />
                        <div class="meta">
                            <div class="name">{{ persona.name }}</div>
                            <div class="tag">{{ persona.is_builtin ? "内置" : "我的" }}</div>
                        </div>
                    </div>

                    <p class="description">
                        {{ persona.description || "暂无描述" }}
                    </p>

                    <div v-if="!persona.is_builtin" class="card-actions">
                        <button @click="startEdit(persona)">编辑</button>
                        <button class="danger" @click="removePersona(persona)">删除</button>
                    </div>
                </article>
            </div>
        </section>

        <aside v-if="editing" class="editor">
            <div class="editor-title">
                <p>{{ editing.id ? "Edit persona" : "New persona" }}</p>
                <h3>{{ editing.id ? "编辑人格" : "新建人格" }}</h3>
            </div>
            <PersonaForm
                :persona="editing"
                :submitText="editing.id ? '保存修改' : '创建人格'"
                @submit="savePersona"
                @cancel="editing = null"
            />
        </aside>
    </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import axios from "../api/axios"
import PersonaForm from "../components/personas/PersonaForm.vue"

const personas = ref([])
const editing = ref(null)

async function fetchPersonas() {
    const res = await axios.get("/api/personas/")
    personas.value = res.data
}

function startCreate() {
    editing.value = {}
}

function startEdit(persona) {
    editing.value = { ...persona }
}

async function savePersona(payload) {
    const config = {
        headers: {
            "Content-Type": "multipart/form-data"
        }
    }

    if (editing.value?.id) {
        await axios.patch(`/api/personas/${editing.value.id}/`, payload, config)
    } else {
        await axios.post("/api/personas/", payload, config)
    }

    editing.value = null
    await fetchPersonas()
}

async function removePersona(persona) {
    if (!confirm(`删除人格「${persona.name}」？`)) return

    await axios.delete(`/api/personas/${persona.id}/`)
    await fetchPersonas()
}

onMounted(fetchPersonas)
</script>

<style scoped>
.persona-page {
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: flex;
    gap: 16px;
    overflow: hidden;
}

.library,
.editor {
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.library {
    flex: 1;
    min-width: 0;
    padding: 24px;
    overflow-y: auto;
}

.header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    margin-bottom: 20px;
}

p {
    margin: 0;
}

.header p,
.editor-title p {
    margin-bottom: 6px;
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

.header button,
.card-actions button {
    border-radius: 16px;
    padding: 11px 15px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: white;
    cursor: pointer;
    font-weight: 900;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.2);
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 14px;
}

.persona-card {
    min-width: 0;
    padding: 16px;
    border: 1px solid rgba(171, 215, 251, 0.34);
    border-radius: 18px;
    background: rgba(249, 242, 239, 0.76);
    box-shadow: 0 10px 24px rgba(164, 109, 78, 0.07);
}

.topline {
    display: flex;
    align-items: center;
    gap: 12px;
}

.avatar {
    width: 58px;
    height: 58px;
    flex: 0 0 auto;
    border: 3px solid rgba(255, 255, 255, 0.82);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 10px 22px rgba(164, 109, 78, 0.12);
}

.meta {
    min-width: 0;
}

.name {
    overflow: hidden;
    color: #4c4038;
    font-size: 17px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.tag {
    display: inline-flex;
    margin-top: 7px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(171, 215, 251, 0.45);
    color: #467399;
    font-size: 12px;
    font-weight: 800;
}

.description {
    min-height: 46px;
    margin-top: 14px;
    color: var(--color-muted);
    line-height: 1.55;
    display: -webkit-box;
    overflow: hidden;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.card-actions {
    display: flex;
    gap: 8px;
    margin-top: 14px;
}

.card-actions button {
    box-shadow: none;
}

.card-actions .danger {
    background: #ef7f68;
}

.editor {
    width: min(380px, 36vw);
    min-width: 320px;
    padding: 24px;
    overflow-y: auto;
}

.editor-title {
    margin-bottom: 18px;
}

@media (max-width: 920px) {
    .persona-page {
        flex-direction: column;
    }

    .editor {
        width: 100%;
        min-width: 0;
    }
}
</style>
