<template>
    <div class="play-page">
        <GomokuGame
            v-if="stage === 'game' && selectedPersona"
            :persona="selectedPersona"
            @back="stage = 'persona'"
        />

        <section v-else class="selection-panel">
            <header class="page-header">
                <button
                    v-if="stage === 'persona'"
                    class="back-button"
                    type="button"
                    @click="stage = 'catalog'"
                >
                    ← 返回游戏
                </button>
                <div>
                    <p class="eyebrow">PLAY TOGETHER</p>
                    <h1>{{ stage === "catalog" ? "和 AI 玩点什么？" : "选择你的对手" }}</h1>
                    <p class="subtitle">
                        {{ stage === "catalog"
                            ? "在轻松对局里继续聊天，看看熟悉的人格会有怎样的棋风。"
                            : "选择一个已有 AI 人格开始五子棋，本页不会创建新人格。"
                        }}
                    </p>
                </div>
            </header>

            <div v-if="stage === 'catalog'" class="game-grid">
                <button
                    v-for="game in games"
                    :key="game.id"
                    class="game-card"
                    :class="{ disabled: !game.available }"
                    type="button"
                    :disabled="!game.available"
                    @click="selectGame(game)"
                >
                    <span class="game-art" :class="game.id">
                        <span>{{ game.symbol }}</span>
                    </span>
                    <span class="game-info">
                        <span class="game-title-row">
                            <strong>{{ game.name }}</strong>
                            <em>{{ game.available ? "可游玩" : "即将开放" }}</em>
                        </span>
                        <span class="game-description">{{ game.description }}</span>
                    </span>
                </button>
            </div>

            <div v-else class="persona-area">
                <div v-if="loading" class="empty-state">正在邀请 AI 入场…</div>
                <div v-else-if="loadError" class="empty-state error">
                    <span>{{ loadError }}</span>
                    <button type="button" @click="fetchPersonas">重新加载</button>
                </div>
                <div v-else class="persona-grid">
                    <button
                        v-for="persona in personas"
                        :key="persona.id"
                        class="persona-card"
                        type="button"
                        @click="startGame(persona)"
                    >
                        <img :src="persona.avatar_url || persona.avatar || '/avatars/default.jpg'" alt="" />
                        <span class="persona-copy">
                            <strong>{{ persona.name }}</strong>
                            <span>{{ persona.description || "等你落下第一枚棋子。" }}</span>
                        </span>
                        <span class="challenge">对局 →</span>
                    </button>
                </div>
            </div>
        </section>
    </div>
</template>

<script setup>
import { ref } from "vue"
import axios from "../api/axios"
import GomokuGame from "../components/games/GomokuGame.vue"

const stage = ref("catalog")
const personas = ref([])
const selectedPersona = ref(null)
const loading = ref(false)
const loadError = ref("")

const games = [
    {
        id: "gomoku",
        name: "五子棋",
        symbol: "● ○",
        description: "执黑先行，在交谈之间连成五子。",
        available: true,
    },
    {
        id: "idiom",
        name: "成语接龙",
        symbol: "成",
        description: "一词接一词，考验词汇与临场反应。",
        available: false,
    },
    {
        id: "poetry",
        name: "飞花令",
        symbol: "花",
        description: "以诗会友，在限定字中来回唱和。",
        available: false,
    },
]

async function selectGame(game) {
    if (!game.available) return
    stage.value = "persona"
    if (!personas.value.length) {
        await fetchPersonas()
    }
}

async function fetchPersonas() {
    loading.value = true
    loadError.value = ""
    try {
        const response = await axios.get("/api/personas/")
        personas.value = response.data
    } catch (error) {
        console.error(error)
        loadError.value = "AI 人格列表加载失败"
    } finally {
        loading.value = false
    }
}

function startGame(persona) {
    selectedPersona.value = persona
    stage.value = "game"
}
</script>

<style scoped>
.play-page {
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: 100%;
    overflow: hidden;
}

.selection-panel {
    height: 100%;
    padding: clamp(22px, 4vw, 46px);
    overflow-y: auto;
    background: rgba(255, 255, 255, 0.7);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.page-header {
    max-width: 760px;
    margin-bottom: 30px;
}

.back-button {
    margin-bottom: 24px;
    padding: 9px 13px;
    border-radius: 12px;
    color: #76685f;
    background: rgba(249, 242, 239, 0.9);
    cursor: pointer;
    font-weight: 800;
}

.eyebrow {
    margin: 0 0 8px;
    color: var(--color-primary);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0.15em;
}

h1 {
    margin: 0;
    color: #40362f;
    font-size: clamp(30px, 4vw, 48px);
    line-height: 1.15;
}

.subtitle {
    margin: 14px 0 0;
    color: var(--color-muted);
    line-height: 1.7;
}

.game-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 18px;
}

.game-card {
    min-width: 0;
    min-height: 330px;
    padding: 0;
    overflow: hidden;
    border: 1px solid rgba(249, 140, 83, 0.16);
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.84);
    color: var(--color-text);
    text-align: left;
    cursor: pointer;
    box-shadow: 0 14px 32px rgba(164, 109, 78, 0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.game-card:not(.disabled):hover {
    transform: translateY(-4px);
    box-shadow: 0 22px 42px rgba(164, 109, 78, 0.16);
}

.game-card.disabled {
    opacity: 0.62;
    cursor: default;
}

.game-art {
    min-height: 190px;
    display: grid;
    place-items: center;
    font-family: Georgia, serif;
    font-size: 40px;
    font-weight: 900;
}

.game-art.gomoku {
    color: #4b3526;
    background:
        linear-gradient(rgba(255,255,255,.16), rgba(255,255,255,.16)),
        repeating-linear-gradient(0deg, transparent 0 22px, rgba(86,55,30,.18) 23px),
        repeating-linear-gradient(90deg, transparent 0 22px, rgba(86,55,30,.18) 23px),
        #e8bd7c;
}

.game-art.idiom {
    color: #855244;
    background: linear-gradient(135deg, #f8d7c3, #fff5ed);
}

.game-art.poetry {
    color: #5e7657;
    background: linear-gradient(135deg, #dce9c1, #f7fbef);
}

.game-info {
    padding: 20px;
    display: block;
}

.game-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.game-title-row strong {
    color: #463a33;
    font-size: 21px;
}

.game-title-row em {
    padding: 5px 9px;
    border-radius: 999px;
    color: #b05d37;
    background: rgba(252, 206, 180, 0.5);
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
}

.game-description {
    margin-top: 12px;
    display: block;
    color: var(--color-muted);
    font-size: 14px;
    line-height: 1.6;
}

.persona-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 14px;
}

.persona-card {
    min-width: 0;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid rgba(171, 215, 251, 0.42);
    border-radius: 19px;
    background: rgba(255, 255, 255, 0.84);
    color: var(--color-text);
    text-align: left;
    cursor: pointer;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.persona-card:hover {
    transform: translateY(-2px);
    border-color: rgba(249, 140, 83, 0.45);
    box-shadow: 0 14px 28px rgba(164, 109, 78, 0.12);
}

.persona-card img {
    width: 60px;
    height: 60px;
    flex: 0 0 auto;
    border-radius: 18px;
    object-fit: cover;
}

.persona-copy {
    min-width: 0;
    flex: 1;
    display: grid;
    gap: 5px;
}

.persona-copy strong {
    color: #463a33;
    font-size: 16px;
}

.persona-copy span {
    overflow: hidden;
    color: var(--color-muted);
    font-size: 13px;
    line-height: 1.45;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.challenge {
    flex: 0 0 auto;
    color: var(--color-primary);
    font-size: 13px;
    font-weight: 900;
}

.empty-state {
    min-height: 220px;
    display: grid;
    place-items: center;
    color: var(--color-muted);
}

.empty-state.error {
    align-content: center;
    gap: 12px;
}

.empty-state button {
    padding: 10px 16px;
    border-radius: 12px;
    color: white;
    background: var(--color-primary);
    cursor: pointer;
}

@media (max-width: 980px) {
    .game-grid {
        grid-template-columns: 1fr;
    }

    .game-card {
        min-height: 0;
        display: grid;
        grid-template-columns: minmax(160px, 34%) 1fr;
    }

    .game-art {
        min-height: 170px;
    }
}

@media (max-width: 560px) {
    .selection-panel {
        padding: 20px;
    }

    .game-card {
        display: block;
    }
}
</style>

