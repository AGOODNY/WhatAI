<template>
    <div class="idiom-layout">
        <section class="idiom-panel">
            <header class="game-header">
                <div class="title-wrap">
                    <button class="back-button" type="button" @click="$emit('back')">←</button>
                    <div>
                        <p>成语接龙 · 同音同调</p>
                        <h2>与 {{ persona.name }} 对局</h2>
                    </div>
                </div>
                <button
                    class="restart-button"
                    type="button"
                    :disabled="startPending"
                    @click="startGame"
                >
                    重新开局
                </button>
            </header>

            <div class="status-strip" :class="{ finished: winner, urgent: timeLeft <= 5 && !winner }">
                <div class="turn-copy">
                    <span class="turn-dot" :class="turn"></span>
                    <div>
                        <small>{{ roundLabel }}</small>
                        <strong>{{ statusText }}</strong>
                    </div>
                </div>
                <div
                    v-if="turn === 'user' || turn === 'ai'"
                    class="timer"
                    :class="{ urgent: timeLeft <= 5 }"
                    :style="timerStyle"
                    role="timer"
                    :aria-label="`剩余 ${timeLeft} 秒`"
                >
                    <span>{{ timeLeft }}</span>
                </div>
                <div v-else class="timer complete">
                    <span>✓</span>
                </div>
            </div>

            <div ref="chainContainer" class="chain-scroll">
                <div v-if="startPending" class="opening-state">
                    <span class="opening-seal">成</span>
                    <strong>{{ persona.name }} 正在挑选开场成语…</strong>
                </div>

                <TransitionGroup v-else name="cascade" tag="div" class="chain-list" appear>
                    <article
                        v-for="(item, index) in chain"
                        :key="item.id"
                        class="idiom-card"
                        :class="item.player"
                    >
                        <div class="card-meta">
                            <span class="round-number">{{ String(index + 1).padStart(2, "0") }}</span>
                            <span>{{ item.player === "ai" ? persona.name : "你" }}</span>
                        </div>
                        <div class="word-tiles" :aria-label="item.word">
                            <span
                                v-for="(character, charIndex) in [...item.word]"
                                :key="`${item.id}-${charIndex}`"
                                :class="{ link: index > 0 && charIndex === 0 }"
                            >
                                {{ character }}
                            </span>
                        </div>
                    </article>
                </TransitionGroup>
            </div>

            <footer class="rule-hint">
                <span>同音同调可接</span>
                <i></i>
                <span>同音不同调不可接</span>
                <i></i>
                <span>成语不可重复</span>
            </footer>
        </section>

        <section class="chat-panel">
            <header class="chat-header">
                <img :src="avatarUrl" alt="" />
                <div>
                    <strong>{{ persona.name }}</strong>
                    <span>
                        <i :class="{ thinking: chatPending || gamePending || startPending }"></i>
                        {{ chatStateText }}
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
                    <img v-if="message.role === 'ai'" :src="avatarUrl" alt="" />
                    <div>
                        <span class="speaker">{{ message.role === "ai" ? persona.name : "你" }}</span>
                        <p>{{ message.content }}</p>
                    </div>
                </div>
                <div v-if="showTyping" class="message ai">
                    <img :src="avatarUrl" alt="" />
                    <div>
                        <span class="speaker">{{ persona.name }}</span>
                        <p class="typing"><i></i><i></i><i></i></p>
                    </div>
                </div>
            </div>

            <form class="chat-input" @submit.prevent="smartSend">
                <input
                    v-model="chatText"
                    type="text"
                    maxlength="1000"
                    :disabled="inputDisabled"
                    :placeholder="inputPlaceholder"
                />
                <div class="input-actions">
                    <button
                        class="chat-button"
                        type="button"
                        :disabled="inputDisabled || !chatText.trim()"
                        @click="sendChat"
                    >
                        聊天
                    </button>
                    <button
                        v-if="turn === 'user' && !winner"
                        class="idiom-button"
                        type="button"
                        :disabled="inputDisabled || !chatText.trim()"
                        @click="submitIdiom"
                    >
                        接龙
                    </button>
                </div>
            </form>
            <p class="input-tip">
                {{ turn === "user" && !winner
                    ? "输入四字成语后按回车会直接接龙；其他内容会作为聊天发送"
                    : "现在可以继续和 AI 聊天"
                }}
            </p>
        </section>
    </div>
</template>

<script setup>
import {
    computed,
    nextTick,
    onBeforeUnmount,
    onMounted,
    ref,
} from "vue"
import axios from "../../api/axios"

const props = defineProps({
    persona: {
        type: Object,
        required: true,
    },
})

defineEmits(["back"])

const TURN_SECONDS = 30
const chain = ref([])
const messages = ref([])
const turn = ref("loading")
const winner = ref("")
const timeLeft = ref(TURN_SECONDS)
const gameToken = ref("")
const chatText = ref("")
const startPending = ref(false)
const gamePending = ref(false)
const chatPending = ref(false)
const chainContainer = ref(null)
const messageContainer = ref(null)

let chainId = 0
let messageId = 0
let timerHandle = null
let deadline = 0
let matchVersion = 0
let gameAbortController = null
let chatAbortController = null

const avatarUrl = computed(() => (
    props.persona.avatar_url
    || props.persona.avatar
    || "/avatars/default.jpg"
))

const roundLabel = computed(() => {
    const completed = chain.value.filter(item => item.player === "user").length
    return completed ? `第 ${completed + 1} 轮` : "开场"
})

const statusText = computed(() => {
    if (winner.value === "user") return "你赢了这局接龙"
    if (winner.value === "ai") return `${props.persona.name} 赢得了这一局`
    if (startPending.value) return "正在准备对局"
    if (turn.value === "ai") return `${props.persona.name} 正在想成语`
    if (turn.value === "user") return "轮到你接龙"
    if (turn.value === "error") return "对局暂时无法开始"
    return "本局已结束"
})

const chatStateText = computed(() => {
    if (startPending.value) return "正在发起挑战…"
    if (chatPending.value) return "正在回复你…"
    if (gamePending.value) return "正在思考下一个成语…"
    if (winner.value) return "对局结束，还可以继续聊天"
    return "一边接龙，一边陪你聊天"
})

const timerStyle = computed(() => ({
    "--timer-angle": `${Math.max(0, timeLeft.value / TURN_SECONDS) * 360}deg`,
}))

const showTyping = computed(() => (
    startPending.value || chatPending.value || gamePending.value
))

const inputDisabled = computed(() => (
    startPending.value
    || gamePending.value
    || chatPending.value
    || !gameToken.value
))

const inputPlaceholder = computed(() => {
    if (turn.value === "user" && !winner.value) return "输入成语，或问问规则、聊点别的…"
    return "和对方聊聊刚才的接龙…"
})

onMounted(startGame)

onBeforeUnmount(() => {
    matchVersion += 1
    clearTurnTimer()
    gameAbortController?.abort()
    chatAbortController?.abort()
})

async function startGame() {
    matchVersion += 1
    const version = matchVersion
    clearTurnTimer()
    gameAbortController?.abort()
    chatAbortController?.abort()

    chain.value = []
    messages.value = []
    winner.value = ""
    turn.value = "loading"
    timeLeft.value = TURN_SECONDS
    gameToken.value = ""
    chatText.value = ""
    startPending.value = true
    gamePending.value = false
    chatPending.value = false

    try {
        const response = await axios.post("/api/games/idiom/start/", {
            persona_id: props.persona.id,
            history: [],
        })
        if (version !== matchVersion) return

        gameToken.value = response.data.game_token
        chain.value = (response.data.chain || []).map(item => ({
            ...item,
            id: ++chainId,
        }))
        addMessage(
            "ai",
            response.data.reply || `我先来：${chain.value[0]?.word}。该你了。`,
        )
        startPending.value = false
        startTurn("user")
        await scrollChainToBottom()
    } catch (error) {
        if (version !== matchVersion) return
        console.error(error)
        startPending.value = false
        turn.value = "error"
        addMessage(
            "ai",
            error.response?.data?.error
                ? `开局失败：${error.response.data.error}`
                : "这局没能顺利开始，请点“重新开局”再试一次。",
        )
    }
}

function startTurn(side) {
    if (winner.value) return
    clearTurnTimer()
    turn.value = side
    timeLeft.value = TURN_SECONDS
    deadline = Date.now() + TURN_SECONDS * 1000
    timerHandle = window.setInterval(updateClock, 200)
}

function resumeUserTurn(previousDeadline) {
    clearTurnTimer()
    turn.value = "user"
    deadline = previousDeadline
    updateClock()
    if (!winner.value && timeLeft.value > 0) {
        timerHandle = window.setInterval(updateClock, 200)
    }
}

function updateClock() {
    const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
    timeLeft.value = remaining
    if (remaining === 0 && (turn.value === "user" || turn.value === "ai")) {
        handleTimeout(turn.value)
    }
}

function clearTurnTimer() {
    if (timerHandle) {
        window.clearInterval(timerHandle)
        timerHandle = null
    }
}

async function handleTimeout(side) {
    if (winner.value || turn.value !== side) return

    clearTurnTimer()
    winner.value = side === "user" ? "ai" : "user"
    turn.value = "finished"
    gamePending.value = false
    gameAbortController?.abort()
    matchVersion += 1

    const fallback = side === "user"
        ? "时间到，这局归我。"
        : "我超时了，这局算你赢。"
    try {
        const response = await axios.post("/api/games/idiom/respond/", {
            persona_id: props.persona.id,
            game_token: gameToken.value,
            chain: serializableChain(),
            history: serializableHistory(),
            action: "timeout",
            timed_out: side,
            message: `${side === "user" ? "用户" : "AI"}思考超时。`,
        })
        addMessage("ai", response.data.reply || fallback)
    } catch (error) {
        console.error(error)
        addMessage("ai", fallback)
    }
}

function smartSend() {
    const content = chatText.value.trim()
    if (!content) return
    if (turn.value === "user" && !winner.value && /^[\u3400-\u9fff]{4}$/.test(content)) {
        submitIdiom()
    } else {
        sendChat()
    }
}

async function submitIdiom() {
    const content = chatText.value.trim()
    if (
        !content
        || turn.value !== "user"
        || winner.value
        || inputDisabled.value
    ) return

    const version = matchVersion
    const userDeadline = deadline
    chatText.value = ""
    addMessage("user", content)
    gamePending.value = true
    startTurn("ai")
    gameAbortController = new AbortController()

    try {
        const response = await axios.post(
            "/api/games/idiom/respond/",
            {
                persona_id: props.persona.id,
                game_token: gameToken.value,
                chain: serializableChain(),
                history: serializableHistory(),
                action: "submit",
                message: content,
            },
            { signal: gameAbortController.signal },
        )
        if (version !== matchVersion) return

        if (!response.data.accepted) {
            gamePending.value = false
            addMessage("ai", response.data.reply || response.data.error || "这次没有接上。")
            resumeUserTurn(userDeadline)
            return
        }

        chain.value.push({
            id: ++chainId,
            word: response.data.user_word,
            player: "user",
        })
        await scrollChainToBottom()

        if (response.data.winner === "user" || !response.data.ai_word) {
            clearTurnTimer()
            gamePending.value = false
            winner.value = "user"
            turn.value = "finished"
            addMessage("ai", response.data.reply || "这回我接不上了，你赢。")
            return
        }

        await wait(650 + Math.random() * 650)
        if (version !== matchVersion || winner.value) return

        chain.value.push({
            id: ++chainId,
            word: response.data.ai_word,
            player: "ai",
        })
        gamePending.value = false
        addMessage("ai", response.data.reply || `我接：${response.data.ai_word}。`)
        await scrollChainToBottom()
        startTurn("user")
    } catch (error) {
        if (version !== matchVersion || error.code === "ERR_CANCELED") return
        console.error(error)
        gamePending.value = false
        addMessage(
            "ai",
            error.response?.data?.error
                ? `这轮出了点问题：${error.response.data.error}`
                : "我刚才走神了，这个成语没有记入，重新来一次。",
        )
        resumeUserTurn(userDeadline)
    } finally {
        if (version === matchVersion) {
            gamePending.value = false
            gameAbortController = null
        }
    }
}

async function sendChat() {
    const content = chatText.value.trim()
    if (!content || inputDisabled.value) return

    chatText.value = ""
    addMessage("user", content)
    chatPending.value = true
    chatAbortController = new AbortController()

    try {
        const response = await axios.post(
            "/api/games/idiom/respond/",
            {
                persona_id: props.persona.id,
                game_token: gameToken.value,
                chain: serializableChain(),
                history: serializableHistory(),
                action: "chat",
                message: content,
            },
            { signal: chatAbortController.signal },
        )
        addMessage("ai", response.data.reply || "嗯，我听着。")
    } catch (error) {
        if (error.code === "ERR_CANCELED") return
        console.error(error)
        addMessage(
            "ai",
            error.response?.data?.error
                ? `聊天出了点问题：${error.response.data.error}`
                : "刚才那句话没接住，再说一次？",
        )
    } finally {
        chatPending.value = false
        chatAbortController = null
    }
}

function serializableChain() {
    return chain.value.map(({ word, player }) => ({ word, player }))
}

function serializableHistory() {
    return messages.value.map(({ role, content }) => ({ role, content }))
}

function addMessage(role, content) {
    if (!content) return
    messages.value.push({
        id: ++messageId,
        role,
        content,
    })
    scrollMessagesToBottom()
}

async function scrollMessagesToBottom() {
    await nextTick()
    const el = messageContainer.value
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
}

async function scrollChainToBottom() {
    await nextTick()
    const el = chainContainer.value
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
}

function wait(milliseconds) {
    return new Promise(resolve => window.setTimeout(resolve, milliseconds))
}
</script>

<style scoped>
.idiom-layout {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(310px, 0.65fr);
    gap: 16px;
}

.idiom-panel,
.chat-panel {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.76);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.idiom-panel {
    display: grid;
    grid-template-rows: auto auto minmax(0, 1fr) auto;
    background:
        radial-gradient(circle at 15% 5%, rgba(250, 207, 175, 0.34), transparent 26%),
        linear-gradient(155deg, rgba(255, 253, 249, 0.94), rgba(251, 244, 236, 0.82));
}

.game-header,
.chat-header {
    padding: 20px 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid rgba(207, 177, 157, 0.22);
}

.title-wrap {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 13px;
}

.back-button {
    width: 38px;
    height: 38px;
    flex: 0 0 auto;
    border-radius: 12px;
    color: #806c5f;
    background: rgba(246, 235, 226, 0.88);
    cursor: pointer;
    font-size: 20px;
    font-weight: 900;
}

.title-wrap p {
    margin: 0 0 3px;
    color: #b26b48;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.08em;
}

.title-wrap h2 {
    margin: 0;
    overflow: hidden;
    color: #463a33;
    font-size: 19px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.restart-button {
    padding: 9px 13px;
    flex: 0 0 auto;
    border: 1px solid rgba(204, 151, 119, 0.25);
    border-radius: 12px;
    color: #9e5b3d;
    background: rgba(255, 249, 244, 0.9);
    cursor: pointer;
    font-size: 12px;
    font-weight: 900;
}

.restart-button:disabled {
    cursor: default;
    opacity: 0.55;
}

.status-strip {
    margin: 16px 20px 4px;
    padding: 12px 14px 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    border: 1px solid rgba(236, 172, 132, 0.24);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
}

.status-strip.urgent {
    border-color: rgba(221, 96, 76, 0.35);
    background: rgba(255, 244, 240, 0.88);
}

.status-strip.finished {
    border-color: rgba(123, 173, 135, 0.28);
    background: rgba(244, 251, 244, 0.82);
}

.turn-copy {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 11px;
}

.turn-copy div {
    min-width: 0;
    display: grid;
    gap: 2px;
}

.turn-copy small {
    color: #a58c7b;
    font-size: 10px;
    font-weight: 800;
}

.turn-copy strong {
    overflow: hidden;
    color: #54453b;
    font-size: 14px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.turn-dot {
    width: 10px;
    height: 10px;
    flex: 0 0 auto;
    border-radius: 50%;
    background: #c7bbb3;
    box-shadow: 0 0 0 5px rgba(199, 187, 179, 0.14);
}

.turn-dot.user {
    background: #ed8b5b;
    box-shadow: 0 0 0 5px rgba(237, 139, 91, 0.14);
}

.turn-dot.ai {
    background: #72a8cf;
    box-shadow: 0 0 0 5px rgba(114, 168, 207, 0.14);
}

.timer {
    width: 48px;
    height: 48px;
    position: relative;
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: conic-gradient(#ed8b5b var(--timer-angle), rgba(222, 207, 197, 0.34) 0);
    transition: background 0.2s linear, transform 0.2s ease;
}

.timer::before {
    position: absolute;
    inset: 4px;
    border-radius: inherit;
    background: #fffaf6;
    content: "";
}

.timer span {
    position: relative;
    color: #76594a;
    font-size: 15px;
    font-variant-numeric: tabular-nums;
    font-weight: 900;
}

.timer.urgent {
    animation: timer-pulse 0.8s ease-in-out infinite;
    background: conic-gradient(#df5e4a var(--timer-angle), rgba(223, 94, 74, 0.14) 0);
}

.timer.complete {
    background: #8fbc96;
}

.timer.complete span {
    color: white;
}

.chain-scroll {
    min-height: 0;
    padding: 18px 28px 28px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(189, 149, 123, 0.35) transparent;
}

.chain-list {
    display: grid;
    gap: 13px;
}

.idiom-card {
    width: min(78%, 430px);
    padding: 13px 15px 15px;
    position: relative;
    border: 1px solid rgba(221, 175, 143, 0.3);
    border-radius: 19px;
    background: rgba(255, 255, 255, 0.87);
    box-shadow: 0 10px 24px rgba(141, 98, 70, 0.08);
}

.idiom-card.ai {
    justify-self: start;
}

.idiom-card.user {
    justify-self: end;
    border-color: rgba(120, 172, 207, 0.3);
    background: rgba(244, 250, 255, 0.92);
}

.idiom-card:not(:last-child)::after {
    width: 1px;
    height: 14px;
    position: absolute;
    right: 25px;
    bottom: -14px;
    background: linear-gradient(#d8bca9, transparent);
    content: "";
}

.idiom-card.user:not(:last-child)::after {
    right: auto;
    left: 25px;
}

.card-meta {
    margin-bottom: 9px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    color: #a18877;
    font-size: 10px;
    font-weight: 800;
}

.round-number {
    color: #d48b65;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.08em;
}

.word-tiles {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
}

.word-tiles span {
    aspect-ratio: 1;
    display: grid;
    place-items: center;
    border: 1px solid rgba(220, 176, 146, 0.24);
    border-radius: 13px;
    color: #654536;
    background:
        linear-gradient(145deg, rgba(255,255,255,.82), rgba(252,237,226,.7));
    font-family: "STKaiti", "KaiTi", "Microsoft YaHei", serif;
    font-size: clamp(21px, 2.25vw, 31px);
    font-weight: 900;
    box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.42);
}

.idiom-card.user .word-tiles span {
    border-color: rgba(133, 180, 211, 0.24);
    color: #3e5e73;
    background: linear-gradient(145deg, #fff, #eaf5fc);
}

.word-tiles span.link {
    animation: link-glow 1.1s ease-out;
}

.opening-state {
    min-height: 260px;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 16px;
    color: #9a8171;
    font-size: 13px;
}

.opening-seal {
    width: 66px;
    height: 66px;
    display: grid;
    place-items: center;
    border: 2px solid rgba(197, 101, 66, 0.65);
    border-radius: 18px 14px 20px 12px;
    color: #bb6445;
    font-family: "STKaiti", "KaiTi", serif;
    font-size: 36px;
    font-weight: 900;
    animation: seal-breathe 1.5s ease-in-out infinite;
}

.rule-hint {
    padding: 12px 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 9px;
    border-top: 1px solid rgba(207, 177, 157, 0.2);
    color: #9c8678;
    background: rgba(255, 252, 248, 0.66);
    font-size: 10px;
    font-weight: 700;
}

.rule-hint i {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: #d6b9a6;
}

.chat-panel {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr) auto auto;
}

.chat-header {
    justify-content: flex-start;
}

.chat-header img {
    width: 45px;
    height: 45px;
    flex: 0 0 auto;
    border-radius: 14px;
    object-fit: cover;
}

.chat-header > div {
    min-width: 0;
    display: grid;
    gap: 4px;
}

.chat-header strong {
    color: #493d35;
    font-size: 15px;
}

.chat-header span {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #99877a;
    font-size: 11px;
}

.chat-header i {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #82bc8c;
}

.chat-header i.thinking {
    background: #ef9b65;
    animation: status-blink 1s ease-in-out infinite;
}

.messages {
    min-height: 0;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    overflow-y: auto;
}

.message {
    display: flex;
    align-items: flex-start;
    gap: 9px;
}

.message.user {
    flex-direction: row-reverse;
}

.message > img {
    width: 30px;
    height: 30px;
    flex: 0 0 auto;
    border-radius: 10px;
    object-fit: cover;
}

.message > div {
    max-width: 82%;
    display: grid;
    gap: 4px;
}

.message.user > div {
    justify-items: end;
}

.speaker {
    color: #aa9789;
    font-size: 9px;
    font-weight: 800;
}

.message p {
    margin: 0;
    padding: 9px 11px;
    border-radius: 5px 15px 15px 15px;
    color: #5b4b42;
    background: #f7eee8;
    font-size: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
}

.message.user p {
    border-radius: 15px 5px 15px 15px;
    color: #3f596b;
    background: #e8f3fa;
}

.typing {
    min-width: 48px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.typing i {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #bb9d8b;
    animation: typing-bounce 1s ease-in-out infinite;
}

.typing i:nth-child(2) {
    animation-delay: 0.15s;
}

.typing i:nth-child(3) {
    animation-delay: 0.3s;
}

.chat-input {
    margin: 0 14px;
    padding: 7px;
    display: flex;
    align-items: center;
    gap: 7px;
    border: 1px solid rgba(205, 178, 159, 0.3);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 8px 20px rgba(139, 105, 83, 0.07);
}

.chat-input input {
    min-width: 0;
    padding: 8px 5px 8px 7px;
    flex: 1;
    border: 0;
    outline: none;
    color: #51443d;
    background: transparent;
    font-size: 12px;
}

.input-actions {
    display: flex;
    align-items: center;
    gap: 5px;
}

.input-actions button {
    padding: 9px 11px;
    border-radius: 11px;
    cursor: pointer;
    font-size: 11px;
    font-weight: 900;
}

.input-actions button:disabled {
    cursor: default;
    opacity: 0.42;
}

.chat-button {
    color: #8b6a59;
    background: #f5ece6;
}

.idiom-button {
    color: white;
    background: linear-gradient(135deg, #ef9564, #df754d);
    box-shadow: 0 5px 12px rgba(221, 116, 76, 0.22);
}

.input-tip {
    margin: 7px 17px 12px;
    color: #aa998f;
    font-size: 9px;
    line-height: 1.4;
}

.cascade-enter-active {
    animation: cascade-in 0.55s cubic-bezier(.16, .9, .3, 1.18);
}

.cascade-leave-active {
    transition: opacity 0.2s ease;
}

.cascade-leave-to {
    opacity: 0;
}

@keyframes cascade-in {
    from {
        opacity: 0;
        transform: translateY(-18px) scale(0.92) rotate(-1.5deg);
    }
    70% {
        transform: translateY(2px) scale(1.015);
    }
    to {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

@keyframes link-glow {
    from {
        box-shadow: 0 0 0 0 rgba(236, 139, 84, 0.5);
    }
    55% {
        box-shadow: 0 0 0 7px rgba(236, 139, 84, 0.08);
    }
    to {
        box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.42);
    }
}

@keyframes timer-pulse {
    50% {
        transform: scale(1.07);
    }
}

@keyframes seal-breathe {
    50% {
        transform: scale(1.04) rotate(1deg);
        opacity: 0.72;
    }
}

@keyframes status-blink {
    50% {
        opacity: 0.35;
    }
}

@keyframes typing-bounce {
    50% {
        transform: translateY(-3px);
        opacity: 0.5;
    }
}

@media (max-width: 980px) {
    .idiom-layout {
        grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
    }

    .chain-scroll {
        padding-inline: 18px;
    }

    .idiom-card {
        width: 86%;
    }
}

@media (max-width: 760px) {
    .idiom-layout {
        height: auto;
        min-height: 100%;
        grid-template-columns: 1fr;
        grid-template-rows: minmax(560px, 72vh) minmax(520px, 66vh);
        overflow-y: auto;
    }
}

@media (max-width: 480px) {
    .game-header,
    .chat-header {
        padding: 16px;
    }

    .status-strip {
        margin-inline: 14px;
    }

    .idiom-card {
        width: 94%;
    }

    .word-tiles {
        gap: 5px;
    }

    .rule-hint {
        flex-wrap: wrap;
    }
}

@media (prefers-reduced-motion: reduce) {
    .cascade-enter-active,
    .timer.urgent,
    .opening-seal,
    .word-tiles span.link,
    .typing i,
    .chat-header i.thinking {
        animation: none;
    }
}
</style>
