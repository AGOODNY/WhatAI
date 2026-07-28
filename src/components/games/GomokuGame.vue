<template>
    <div class="gomoku-layout">
        <section class="board-panel">
            <header class="game-header">
                <div class="title-wrap">
                    <button class="back-button" type="button" @click="$emit('back')">←</button>
                    <div>
                        <p>五子棋 · 你执黑</p>
                        <h2>与 {{ persona.name }} 对局</h2>
                    </div>
                </div>
                <button class="restart-button" type="button" :disabled="pending" @click="restartGame">重新开局</button>
            </header>

            <div class="status-strip" :class="{ finished: winner }">
                <span class="turn-dot" :class="turnClass"></span>
                <strong>{{ statusText }}</strong>
                <span v-if="lastMoveText" class="last-move">最近落子 {{ lastMoveText }}</span>
            </div>

            <div class="board-wrap">
                <div class="board-shell">
                    <div class="board-grid" role="grid" aria-label="十五路五子棋棋盘">
                        <div
                            v-for="cell in flatBoard"
                            :key="`${cell.row}-${cell.col}`"
                            class="board-cell"
                            :class="{
                                edgeTop: cell.row === 0,
                                edgeLeft: cell.col === 0,
                                last: lastMove?.row === cell.row && lastMove?.col === cell.col,
                                playable: canPlace(cell),
                                waiting: pending && !winner && cell.value === 0,
                            }"
                            role="gridcell"
                            :tabindex="canPlace(cell) ? 0 : -1"
                            :aria-label="`${columnLabel(cell.col)}${cell.row + 1}${cell.value ? (cell.value === 1 ? '黑棋' : '白棋') : '空位'}`"
                            :aria-disabled="!canPlace(cell)"
                            @click="handleCellInteraction(cell)"
                            @keydown.enter.prevent="handleCellInteraction(cell)"
                            @keydown.space.prevent="handleCellInteraction(cell)"
                        >
                            <span v-if="cell.value" class="stone" :class="cell.value === 1 ? 'black' : 'white'">
                                <span v-if="lastMove?.row === cell.row && lastMove?.col === cell.col" class="last-marker"></span>
                            </span>
                            <span
                                v-else-if="!winner"
                                class="stone ghost-stone"
                                :class="previewPlayer === 1 ? 'black' : 'white'"
                                aria-hidden="true"
                            ></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="legend">
                <span><i class="legend-stone black"></i>你</span>
                <span><i class="legend-stone white"></i>{{ persona.name }}</span>
                <span class="hint">横、竖或斜线率先连成五子即获胜</span>
            </div>
        </section>

        <section class="chat-panel">
            <header class="chat-header">
                <img :src="persona.avatar_url || persona.avatar || '/avatars/default.jpg'" alt="" />
                <div>
                    <strong>{{ persona.name }}</strong>
                    <span>
                        <i :class="{ thinking: pending }"></i>
                        {{ pending
                            ? (pendingAction === "chat" ? "正在回复你…" : "正在思考棋局…")
                            : "在棋盘边陪你聊天"
                        }}
                    </span>
                </div>
            </header>

            <div ref="messageContainer" class="messages">
                <div
                    v-for="message in messages"
                    :key="message.id"
                    class="message"
                    :class="message.role"
                >
                    <img
                        v-if="message.role === 'ai'"
                        :src="persona.avatar_url || persona.avatar || '/avatars/default.jpg'"
                        alt=""
                    />
                    <div>
                        <span class="speaker">{{ message.role === "ai" ? persona.name : "你" }}</span>
                        <p>{{ message.content }}</p>
                    </div>
                </div>
                <div v-if="pending && pendingAction === 'chat'" class="message ai">
                    <img :src="persona.avatar_url || persona.avatar || '/avatars/default.jpg'" alt="" />
                    <div>
                        <span class="speaker">{{ persona.name }}</span>
                        <p class="typing"><i></i><i></i><i></i></p>
                    </div>
                </div>
            </div>

            <form class="chat-input" @submit.prevent="sendChat">
                <input
                    v-model="chatText"
                    type="text"
                    maxlength="1000"
                    :disabled="pending"
                    placeholder="聊聊这盘棋，或说点别的…"
                />
                <button type="submit" :disabled="pending || !chatText.trim()">发送</button>
            </form>
        </section>
    </div>
</template>

<script setup>
import { computed, nextTick, ref } from "vue"
import axios from "../../api/axios"

const props = defineProps({
    persona: {
        type: Object,
        required: true,
    },
})

defineEmits(["back"])

const SIZE = 15
const board = ref(createBoard())
const messages = ref([])
const pending = ref(false)
const pendingAction = ref("")
const winner = ref("")
const lastMove = ref(null)
const chatText = ref("")
const messageContainer = ref(null)
const stonesSinceAiSpoke = ref(0)
const nextSpeechAt = ref(randomSpeechInterval())
let messageId = 0

startConversation()

const flatBoard = computed(() => (
    board.value.flatMap((row, rowIndex) => (
        row.map((value, colIndex) => ({
            row: rowIndex,
            col: colIndex,
            value,
        }))
    ))
))

const statusText = computed(() => {
    if (winner.value === "user") return "你赢了！漂亮的五子连线"
    if (winner.value === "ai") return `${props.persona.name} 赢得了这一局`
    if (winner.value === "draw") return "棋盘已满，这局平局"
    if (pending.value) return `${props.persona.name} 正在落子`
    return "轮到你落子"
})

const turnClass = computed(() => {
    if (winner.value) return "complete"
    return pending.value ? "white" : "black"
})

const previewPlayer = computed(() => pending.value ? 2 : 1)

const lastMoveText = computed(() => {
    if (!lastMove.value) return ""
    return `${columnLabel(lastMove.value.col)}${lastMove.value.row + 1}`
})

function createBoard() {
    return Array.from({ length: SIZE }, () => Array(SIZE).fill(0))
}

function randomSpeechInterval() {
    return 4 + Math.floor(Math.random() * 4)
}

function resetSpeechCadence() {
    stonesSinceAiSpoke.value = 0
    nextSpeechAt.value = randomSpeechInterval()
}

function columnLabel(col) {
    return String.fromCharCode(65 + col)
}

function canPlace(cell) {
    return cell.value === 0 && !pending.value && !winner.value
}

function handleCellInteraction(cell) {
    if (!canPlace(cell)) return
    placeUserStone(cell.row, cell.col)
}

function startConversation() {
    messages.value = [{
        id: ++messageId,
        role: "ai",
        content: `来吧，你执黑先行。下棋的时候也可以随时和我聊天。`,
    }]
}

async function placeUserStone(row, col) {
    if (pending.value || winner.value || board.value[row][col] !== 0) return

    const previousLastMove = lastMove.value
    board.value[row][col] = 1
    lastMove.value = { row, col, player: 1 }

    if (hasFive(row, col, 1)) {
        winner.value = "user"
        await requestAi({
            action: "chat",
            message: `用户刚刚在 ${columnLabel(col)}${row + 1} 连成五子并获胜。`,
        })
        return
    }

    if (isBoardFull()) {
        winner.value = "draw"
        return
    }

    const completed = await requestAi({
        action: "move",
        message: `用户刚刚落在 ${columnLabel(col)}${row + 1}。`,
    })
    if (!completed) {
        board.value[row][col] = 0
        lastMove.value = previousLastMove
    }
}

async function sendChat() {
    const content = chatText.value.trim()
    if (!content || pending.value) return

    chatText.value = ""
    addMessage("user", content)
    await requestAi({ action: "chat", message: content })
}

async function requestAi({ action, message }) {
    const forceReply = (
        action === "move"
        && stonesSinceAiSpoke.value + 2 >= nextSpeechAt.value
    )
    pendingAction.value = action
    pending.value = true
    await scrollToBottom()

    try {
        const history = messages.value.map(item => ({
            role: item.role,
            content: item.content,
        }))
        const response = await axios.post("/api/games/gomoku/respond/", {
            persona_id: props.persona.id,
            board: board.value,
            history,
            message,
            action,
            force_reply: forceReply,
        })

        const move = response.data.ai_move
        let aiMoved = false
        if (move && board.value[move.row]?.[move.col] === 0) {
            board.value[move.row][move.col] = 2
            lastMove.value = { ...move, player: 2 }
            aiMoved = true

            if (response.data.winner === "ai" || hasFive(move.row, move.col, 2)) {
                winner.value = "ai"
            } else if (isBoardFull()) {
                winner.value = "draw"
            }
        }

        const reply = typeof response.data.reply === "string"
            ? response.data.reply.trim()
            : ""
        if (reply) {
            addMessage("ai", reply)
            resetSpeechCadence()
        } else if (action === "move" && aiMoved) {
            stonesSinceAiSpoke.value += 2
        }
        return true
    } catch (error) {
        console.error(error)
        const detail = error.response?.data?.error
        addMessage("ai", detail ? `这一步出了点问题：${detail}` : "我刚才走神了一下，没能完成这一步，请再试一次。")
        return false
    } finally {
        pending.value = false
        pendingAction.value = ""
        await scrollToBottom()
    }
}

function hasFive(row, col, player) {
    const directions = [[1, 0], [0, 1], [1, 1], [1, -1]]
    return directions.some(([dr, dc]) => {
        let count = 1
        for (const sign of [-1, 1]) {
            let step = 1
            while (
                row + dr * step * sign >= 0
                && row + dr * step * sign < SIZE
                && col + dc * step * sign >= 0
                && col + dc * step * sign < SIZE
                && board.value[row + dr * step * sign][col + dc * step * sign] === player
            ) {
                count += 1
                step += 1
            }
        }
        return count >= 5
    })
}

function isBoardFull() {
    return board.value.every(row => row.every(Boolean))
}

function addMessage(role, content) {
    messages.value.push({
        id: ++messageId,
        role,
        content,
    })
    scrollToBottom()
}

async function scrollToBottom() {
    await nextTick()
    const el = messageContainer.value
    if (el) {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
    }
}

function restartGame() {
    board.value = createBoard()
    winner.value = ""
    lastMove.value = null
    pending.value = false
    pendingAction.value = ""
    chatText.value = ""
    resetSpeechCadence()
    startConversation()
    scrollToBottom()
}
</script>

<style scoped>
.gomoku-layout {
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: 100%;
    display: grid;
    grid-template-columns: minmax(520px, 1.18fr) minmax(340px, 0.82fr);
    gap: 16px;
    overflow: hidden;
}

.board-panel,
.chat-panel {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.board-panel {
    padding: 20px;
    display: flex;
    flex-direction: column;
}

.game-header,
.chat-header {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
}

.title-wrap {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.back-button {
    width: 38px;
    height: 38px;
    flex: 0 0 auto;
    border-radius: 13px;
    background: rgba(249, 242, 239, 0.92);
    color: #6e6058;
    cursor: pointer;
    font-size: 20px;
}

.title-wrap p {
    margin: 0 0 3px;
    color: var(--color-primary);
    font-size: 11px;
    font-weight: 900;
}

.title-wrap h2 {
    overflow: hidden;
    margin: 0;
    color: #443831;
    font-size: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.restart-button {
    flex: 0 0 auto;
    padding: 10px 13px;
    border: 1px solid rgba(249, 140, 83, 0.18);
    border-radius: 13px;
    background: rgba(255, 255, 255, 0.76);
    color: #815e4d;
    cursor: pointer;
    font-size: 13px;
    font-weight: 800;
}

.restart-button:disabled {
    opacity: 0.55;
    cursor: default;
}

.status-strip {
    min-height: 42px;
    margin-top: 16px;
    padding: 10px 13px;
    display: flex;
    align-items: center;
    gap: 9px;
    border-radius: 13px;
    background: rgba(249, 242, 239, 0.82);
    color: #665a52;
    font-size: 13px;
}

.status-strip.finished {
    background: linear-gradient(135deg, rgba(210, 224, 170, 0.44), rgba(171, 215, 251, 0.35));
}

.turn-dot {
    width: 12px;
    height: 12px;
    flex: 0 0 auto;
    border: 2px solid rgba(73, 54, 43, 0.15);
    border-radius: 50%;
    background: #282522;
}

.turn-dot.white {
    background: #fff;
    box-shadow: 0 0 0 1px rgba(73, 54, 43, 0.18);
}

.turn-dot.complete {
    border-color: transparent;
    background: var(--color-primary);
}

.last-move {
    margin-left: auto;
    color: var(--color-muted);
    font-size: 12px;
}

.board-wrap {
    flex: 1;
    min-height: 0;
    padding: 16px 0 10px;
    display: grid;
    place-items: center;
}

.board-shell {
    width: min(100%, calc(100vh - 220px));
    min-width: 300px;
    padding: 18px;
    border: 1px solid rgba(91, 57, 31, 0.25);
    border-radius: 18px;
    background: linear-gradient(135deg, #ecc98f, #d9a85e);
    box-shadow: inset 0 0 28px rgba(91, 57, 31, 0.16), 0 18px 35px rgba(118, 77, 42, 0.18);
}

.board-grid {
    width: 100%;
    aspect-ratio: 1;
    display: grid;
    grid-template-columns: repeat(15, minmax(0, 1fr));
    grid-template-rows: repeat(15, minmax(0, 1fr));
    border-right: 1px solid rgba(76, 48, 25, 0.52);
    border-bottom: 1px solid rgba(76, 48, 25, 0.52);
}

.board-cell {
    position: relative;
    min-width: 0;
    min-height: 0;
    padding: 0;
    border-top: 1px solid rgba(76, 48, 25, 0.52);
    border-left: 1px solid rgba(76, 48, 25, 0.52);
    border-radius: 0;
    background: transparent;
    cursor: default;
    outline: none;
}

.board-cell.playable {
    cursor: pointer;
}

.board-cell.playable:focus-visible {
    z-index: 3;
    box-shadow: inset 0 0 0 2px rgba(249, 140, 83, 0.88);
}

.stone {
    position: absolute;
    z-index: 2;
    inset: 9%;
    border-radius: 50%;
    box-shadow: 1px 3px 5px rgba(57, 39, 24, 0.34);
    pointer-events: none;
}

.stone.black,
.legend-stone.black {
    background: radial-gradient(circle at 35% 30%, #605c58, #161514 68%);
}

.stone.white,
.legend-stone.white {
    border: 1px solid rgba(79, 61, 48, 0.18);
    background: radial-gradient(circle at 35% 30%, #fff, #e8e3dc 72%);
}

.ghost-stone {
    opacity: 0;
    transform: scale(0.82);
    transition: opacity 0.14s ease, transform 0.14s ease;
}

.board-cell.playable:hover .ghost-stone,
.board-cell.playable:focus-visible .ghost-stone,
.board-cell.waiting:hover .ghost-stone {
    opacity: 0.34;
    transform: scale(1);
}

.board-cell.waiting .ghost-stone {
    cursor: wait;
}

.last-marker {
    position: absolute;
    width: 24%;
    height: 24%;
    top: 38%;
    left: 38%;
    border-radius: 50%;
    background: #f06f4a;
    box-shadow: 0 0 0 1px rgba(255,255,255,.6);
}

.legend {
    flex: 0 0 auto;
    min-height: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    color: #766b63;
    font-size: 12px;
}

.legend span {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.legend-stone {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(57, 39, 24, 0.2);
}

.legend .hint {
    margin-left: auto;
    color: var(--color-muted);
}

.chat-panel {
    display: flex;
    flex-direction: column;
}

.chat-header {
    min-height: 74px;
    padding: 12px 18px;
    justify-content: flex-start;
    border-bottom: 1px solid rgba(249, 140, 83, 0.15);
    background: linear-gradient(135deg, rgba(255,255,255,.9), rgba(252,206,180,.32));
}

.chat-header img {
    width: 48px;
    height: 48px;
    flex: 0 0 auto;
    border: 3px solid rgba(255, 255, 255, 0.88);
    border-radius: 16px;
    object-fit: cover;
    box-shadow: 0 8px 16px rgba(164, 109, 78, 0.12);
}

.chat-header div {
    min-width: 0;
    display: grid;
    gap: 5px;
}

.chat-header strong {
    overflow: hidden;
    color: #483c35;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.chat-header span {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-muted);
    font-size: 12px;
}

.chat-header i {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #83b35b;
}

.chat-header i.thinking {
    background: var(--color-primary);
    animation: pulse 1s infinite;
}

.messages {
    flex: 1;
    min-height: 0;
    padding: 20px 16px;
    overflow-y: auto;
    background:
        radial-gradient(circle at 100% 0, rgba(171, 215, 251, 0.16), transparent 18rem),
        radial-gradient(circle at 0 100%, rgba(210, 224, 170, 0.13), transparent 18rem);
}

.message {
    margin-bottom: 18px;
    display: flex;
    align-items: flex-start;
    gap: 9px;
}

.message.user {
    flex-direction: row-reverse;
}

.message > img {
    width: 34px;
    height: 34px;
    flex: 0 0 auto;
    border-radius: 11px;
    object-fit: cover;
}

.message > div {
    max-width: 78%;
}

.speaker {
    margin: 0 4px 4px;
    display: block;
    color: var(--color-muted);
    font-size: 11px;
}

.message.user .speaker {
    text-align: right;
}

.message p {
    margin: 0;
    padding: 10px 12px;
    border: 1px solid rgba(249, 140, 83, 0.1);
    border-radius: 6px 15px 15px;
    background: rgba(255, 255, 255, 0.92);
    color: var(--color-text);
    line-height: 1.58;
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: 0 7px 16px rgba(164, 109, 78, 0.07);
}

.message.user p {
    border-radius: 15px 6px 15px 15px;
    background: linear-gradient(135deg, rgba(252, 206, 180, 0.9), rgba(171, 215, 251, 0.46));
}

.typing {
    display: flex;
    gap: 5px;
}

.typing i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #b6a79e;
    animation: bounce 1.1s infinite;
}

.typing i:nth-child(2) { animation-delay: .15s; }
.typing i:nth-child(3) { animation-delay: .3s; }

.chat-input {
    flex: 0 0 auto;
    min-height: 72px;
    padding: 13px;
    display: flex;
    align-items: center;
    gap: 9px;
    border-top: 1px solid rgba(249, 140, 83, 0.14);
    background: rgba(255, 255, 255, 0.78);
}

.chat-input input {
    flex: 1;
    min-width: 0;
    height: 44px;
    padding: 0 13px;
    border: 1px solid rgba(249, 140, 83, 0.2);
    border-radius: 14px;
    outline: none;
    background: rgba(249, 242, 239, 0.74);
    color: var(--color-text);
}

.chat-input input:focus {
    border-color: rgba(249, 140, 83, 0.52);
    box-shadow: 0 0 0 3px rgba(252, 206, 180, 0.28);
}

.chat-input button {
    height: 44px;
    padding: 0 16px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-primary), #f6a272);
    color: white;
    cursor: pointer;
    font-weight: 900;
}

.chat-input button:disabled,
.chat-input input:disabled {
    opacity: 0.58;
    cursor: default;
}

@keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
}

@keyframes pulse {
    50% { opacity: .4; }
}

@media (max-width: 1050px) {
    .gomoku-layout {
        grid-template-columns: minmax(460px, 1.05fr) minmax(300px, .95fr);
    }

    .board-panel {
        padding: 15px;
    }

    .legend .hint {
        display: none;
    }
}

@media (max-width: 820px) {
    .gomoku-layout {
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }

    .board-panel,
    .chat-panel {
        flex: 0 0 auto;
        overflow: visible;
    }

    .board-wrap {
        min-height: 390px;
    }

    .board-shell {
        width: min(100%, 560px);
    }

    .chat-panel {
        min-height: 520px;
    }

    .messages {
        min-height: 350px;
    }
}

@media (max-width: 520px) {
    .board-panel {
        padding: 12px;
    }

    .board-shell {
        min-width: 0;
        padding: 10px;
    }

    .board-wrap {
        min-height: 320px;
    }

    .restart-button {
        padding: 9px;
    }

    .last-move {
        display: none;
    }
}
</style>
