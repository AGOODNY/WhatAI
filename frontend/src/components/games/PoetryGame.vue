<template>
    <div class="poetry-layout">
        <section class="poetry-panel">
            <header class="game-header">
                <div class="title-wrap">
                    <button class="back-button" type="button" @click="$emit('back')">←</button>
                    <div>
                        <p>飞花令 · 古典诗词</p>
                        <h2>与 {{ persona.name }} 对句</h2>
                    </div>
                </div>
                <button class="restart-button" type="button" :disabled="startPending" @click="startGame">
                    重新开局
                </button>
            </header>

            <div class="target-stage" :class="{ waiting: !target }">
                <span class="target-label">{{ target ? "本局令字" : "等待选字" }}</span>
                <strong v-if="target">{{ target }}</strong>
                <p v-else>{{ phase === "choose_character" ? "请在右侧输入一个汉字" : "先和 AI 商量由谁选字" }}</p>
            </div>

            <div class="status-strip" :class="{ finished: winner, urgent: timeLeft <= 10 && !winner }">
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
                    :class="{ urgent: timeLeft <= 10 }"
                    :style="timerStyle"
                    role="timer"
                    :aria-label="`剩余 ${timeLeft} 秒`"
                >
                    <span>{{ formattedTime }}</span>
                </div>
                <div v-else class="timer complete"><span>{{ winner ? "✓" : "·" }}</span></div>
            </div>

            <div ref="verseContainer" class="verse-scroll">
                <div v-if="startPending" class="opening-state">
                    <span class="opening-seal">令</span>
                    <strong>{{ persona.name }} 正在赴约…</strong>
                </div>
                <div v-else-if="!verses.length" class="empty-verses">
                    <span>花影未落，诗句尚待开场</span>
                </div>
                <TransitionGroup v-else name="cascade" tag="div" class="verse-list" appear>
                    <article
                        v-for="(item, index) in verses"
                        :key="item.id"
                        class="verse-card"
                        :class="[item.player, { newest: index === verses.length - 1 }]"
                    >
                        <div class="card-meta">
                            <span>{{ String(index + 1).padStart(2, "0") }}</span>
                            <em>{{ item.player === "ai" ? persona.name : "你" }}</em>
                        </div>
                        <p :aria-label="item.verse">
                            <template v-for="(part, partIndex) in verseSegments(item.verse)" :key="`${item.id}-${partIndex}`">
                                <mark v-if="part.highlight">{{ part.text }}</mark>
                                <span v-else>{{ part.text }}</span>
                            </template>
                        </p>
                    </article>
                </TransitionGroup>
            </div>

            <footer class="rule-hint">
                <span>必须包含令字</span><i></i>
                <span>须说完整一句</span><i></i>
                <span>仅限古典诗词曲</span><i></i>
                <span>诗句不可重复</span>
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
                <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
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
                <textarea
                    ref="chatInput"
                    v-model="chatText"
                    rows="2"
                    maxlength="1000"
                    :readonly="inputDisabled"
                    :aria-readonly="inputDisabled"
                    :placeholder="inputPlaceholder"
                    @keydown.enter.exact.prevent="smartSend"
                ></textarea>
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
                        v-if="!winner && phase !== 'finished'"
                        class="poetry-button"
                        type="submit"
                        :disabled="inputDisabled || !chatText.trim()"
                    >
                        {{ phase === "playing" ? "应答" : "确定" }}
                    </button>
                </div>
            </form>
            <p class="input-tip">{{ inputTip }}</p>
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

const TURN_SECONDS = 120
const AI_MIN_REPLY_MS = 3000
const verses = ref([])
const messages = ref([])
const phase = ref("loading")
const target = ref("")
const turn = ref("loading")
const winner = ref("")
const timeLeft = ref(TURN_SECONDS)
const gameToken = ref("")
const chatText = ref("")
const startPending = ref(false)
const gamePending = ref(false)
const chatPending = ref(false)
const verseContainer = ref(null)
const messageContainer = ref(null)
const chatInput = ref(null)

let nextId = 1
let turnInterval = null
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
    if (phase.value !== "playing" && phase.value !== "finished") return "开局准备"
    const userAnswers = verses.value.filter(item => item.player === "user").length
    return `第 ${userAnswers + (turn.value === "user" ? 1 : 0)} 次应答`
})

const statusText = computed(() => {
    if (winner.value === "user") return "你赢下了这一局"
    if (winner.value === "ai") return `${props.persona.name} 赢下了这一局`
    if (startPending.value) return "正在发起飞花令"
    if (phase.value === "choose_side") return "请决定由谁选字"
    if (phase.value === "choose_character") return "请输入本局令字"
    if (turn.value === "ai") return `${props.persona.name} 正在寻句`
    if (turn.value === "user") return "轮到你说完整诗句"
    return "等待开局"
})

const chatStateText = computed(() => {
    if (startPending.value) return "正在进入对局"
    if (chatPending.value) return "正在回复你"
    if (gamePending.value) return target.value ? "正在想下一句" : "正在回应"
    if (winner.value) return "对局结束，还可以继续聊天"
    if (phase.value === "choose_character") return "等你写下令字"
    if (phase.value === "choose_side") return "等你决定谁选字"
    return turn.value === "user" ? "等你应答" : "在想诗句"
})

const formattedTime = computed(() => {
    const minutes = Math.floor(timeLeft.value / 60)
    const seconds = timeLeft.value % 60
    return `${minutes}:${String(seconds).padStart(2, "0")}`
})

const timerStyle = computed(() => ({
    "--timer-angle": `${Math.max(0, timeLeft.value / TURN_SECONDS) * 360}deg`,
}))

const showTyping = computed(() => startPending.value || chatPending.value || gamePending.value)
const inputDisabled = computed(() => startPending.value || chatPending.value || gamePending.value)

const inputPlaceholder = computed(() => {
    if (phase.value === "choose_side") return "回复“你选字”或“我选字”…"
    if (phase.value === "choose_character") return "输入一个想要的汉字…"
    if (turn.value === "user" && !winner.value) return `说一句含“${target.value}”的完整古典诗词…`
    return "对局之余，也可以聊聊…"
})

const inputTip = computed(() => {
    if (phase.value === "choose_side") return "先决定令字由谁来选"
    if (phase.value === "choose_character") return "仅输入一个汉字，AI 会先用它开场"
    if (turn.value === "user" && !winner.value) return "按回车提交诗句；想闲聊时请点“聊天”"
    return "现在仍然可以继续和 AI 私聊"
})

onMounted(startGame)

onBeforeUnmount(() => {
    matchVersion += 1
    clearTurnTimer()
    gameAbortController?.abort()
    chatAbortController?.abort()
})

async function startGame() {
    const version = ++matchVersion
    clearTurnTimer()
    gameAbortController?.abort()
    chatAbortController?.abort()
    verses.value = []
    messages.value = []
    target.value = ""
    winner.value = ""
    phase.value = "loading"
    turn.value = "loading"
    timeLeft.value = TURN_SECONDS
    gameToken.value = ""
    chatText.value = ""
    startPending.value = true
    gamePending.value = false
    chatPending.value = false
    try {
        const response = await axios.post("/api/games/poetry/start/", {
            persona_id: props.persona.id,
            history: [],
        })
        if (version !== matchVersion) return
        gameToken.value = response.data.game_token
        phase.value = response.data.phase
        turn.value = "choosing"
        addMessage("ai", response.data.reply)
    } catch (error) {
        if (version !== matchVersion) return
        console.error(error)
        phase.value = "choose_side"
        turn.value = "choosing"
        addMessage("ai", error.response?.data?.error || "飞花令暂时没能开局，请重新试一次。")
    } finally {
        if (version === matchVersion) {
            startPending.value = false
            await focusInput()
        }
    }
}

function startTurn(side) {
    clearTurnTimer()
    if (winner.value) return
    turn.value = side
    timeLeft.value = TURN_SECONDS
    deadline = Date.now() + TURN_SECONDS * 1000
    turnInterval = window.setInterval(updateClock, 250)
}

function resumeUserTurn(previousDeadline) {
    clearTurnTimer()
    turn.value = "user"
    deadline = previousDeadline
    updateClock()
    if (!winner.value && timeLeft.value > 0) {
        turnInterval = window.setInterval(updateClock, 250)
    }
}

function updateClock() {
    if (!deadline) return
    const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
    timeLeft.value = remaining
    if (remaining === 0) handleTimeout(turn.value)
}

function clearTurnTimer() {
    if (turnInterval) window.clearInterval(turnInterval)
    turnInterval = null
    deadline = 0
}

async function handleTimeout(side) {
    if (winner.value || !["user", "ai"].includes(side) || turn.value !== side) return
    const version = matchVersion
    clearTurnTimer()
    gameAbortController?.abort()
    gamePending.value = true
    try {
        const response = await axios.post("/api/games/poetry/respond/", {
            persona_id: props.persona.id,
            game_token: gameToken.value,
            verses: serializableVerses(),
            history: serializableHistory(),
            action: "timeout",
            message: "",
            timed_out: side,
        })
        if (version !== matchVersion) return
        if (response.data.game_token) gameToken.value = response.data.game_token
        addMessage("ai", response.data.reply)
        if (response.data.retry_turn === "user") {
            startTurn("user")
        } else {
            winner.value = response.data.winner
            phase.value = "finished"
            turn.value = "finished"
        }
    } catch (error) {
        if (version !== matchVersion) return
        addMessage("ai", error.response?.data?.error || "计时状态没有同步成功，请重新开局。")
        startTurn("user")
    } finally {
        if (version === matchVersion) gamePending.value = false
    }
}

function smartSend() {
    if (!chatText.value.trim() || inputDisabled.value) return
    if (phase.value === "playing" && turn.value !== "user") {
        sendChat()
        return
    }
    if (winner.value || phase.value === "finished") {
        sendChat()
        return
    }
    submitGame()
}

async function submitGame() {
    const content = chatText.value.trim()
    if (!content || inputDisabled.value || !gameToken.value) return
    const version = matchVersion
    const previousDeadline = deadline
    const wasPlaying = phase.value === "playing"
    if (wasPlaying) {
        clearTurnTimer()
        turn.value = "ai"
        timeLeft.value = TURN_SECONDS
        deadline = Date.now() + TURN_SECONDS * 1000
        turnInterval = window.setInterval(updateClock, 250)
    }
    chatText.value = ""
    addMessage("user", content)
    gamePending.value = true
    const startedAt = Date.now()
    gameAbortController = new AbortController()
    try {
        const response = await axios.post(
            "/api/games/poetry/respond/",
            {
                persona_id: props.persona.id,
                game_token: gameToken.value,
                verses: serializableVerses(),
                history: serializableHistory(),
                action: wasPlaying ? "smart" : "choose",
                message: content,
            },
            { signal: gameAbortController.signal },
        )
        if (response.data.ai_verse) {
            await wait(Math.max(0, AI_MIN_REPLY_MS - (Date.now() - startedAt)))
        }
        if (version !== matchVersion) return
        clearTurnTimer()
        if (response.data.game_token) gameToken.value = response.data.game_token
        if (response.data.phase) phase.value = response.data.phase
        if (response.data.target) target.value = response.data.target

        if (Array.isArray(response.data.verses)) {
            verses.value = response.data.verses.map(item => ({ ...item, id: nextId++ }))
        } else if (response.data.accepted && response.data.user_verse) {
            verses.value.push({ id: nextId++, player: "user", verse: response.data.user_verse })
            if (response.data.ai_verse) {
                verses.value.push({ id: nextId++, player: "ai", verse: response.data.ai_verse })
            }
        }
        addMessage("ai", response.data.reply)

        if (response.data.winner) {
            winner.value = response.data.winner
            phase.value = "finished"
            turn.value = "finished"
        } else if (phase.value === "playing") {
            if (response.data.accepted === false && wasPlaying) {
                if (response.data.reset_timer) startTurn("user")
                else resumeUserTurn(previousDeadline)
            } else {
                startTurn("user")
            }
        } else {
            turn.value = "choosing"
        }
        await scrollVersesToBottom()
    } catch (error) {
        if (version !== matchVersion || error.code === "ERR_CANCELED") return
        console.error(error)
        clearTurnTimer()
        addMessage("ai", error.response?.data?.error || "这次没有接稳，请再试一次。")
        if (wasPlaying) resumeUserTurn(previousDeadline)
        else turn.value = "choosing"
    } finally {
        if (version === matchVersion) {
            gamePending.value = false
            gameAbortController = null
            await focusInput()
        }
    }
}

async function sendChat() {
    const content = chatText.value.trim()
    if (!content || inputDisabled.value || !gameToken.value) return
    const version = matchVersion
    chatText.value = ""
    addMessage("user", content)
    chatPending.value = true
    chatAbortController = new AbortController()
    try {
        const response = await axios.post(
            "/api/games/poetry/respond/",
            {
                persona_id: props.persona.id,
                game_token: gameToken.value,
                verses: serializableVerses(),
                history: serializableHistory(),
                action: "chat",
                message: content,
            },
            { signal: chatAbortController.signal },
        )
        if (version !== matchVersion) return
        addMessage("ai", response.data.reply)
    } catch (error) {
        if (version !== matchVersion || error.code === "ERR_CANCELED") return
        console.error(error)
        addMessage("ai", error.response?.data?.error || "刚才走神了，你再说一次？")
    } finally {
        if (version === matchVersion) {
            chatPending.value = false
            chatAbortController = null
            await focusInput()
        }
    }
}

function verseSegments(verse) {
    if (!target.value) return [{ text: verse, highlight: false }]
    const segments = []
    verse.split(target.value).forEach((part, index, all) => {
        if (part) segments.push({ text: part, highlight: false })
        if (index < all.length - 1) segments.push({ text: target.value, highlight: true })
    })
    return segments
}

function serializableVerses() {
    return verses.value.map(({ verse, player }) => ({ verse, player }))
}

function serializableHistory() {
    return messages.value.map(({ role, content }) => ({ role, content })).slice(-24)
}

function addMessage(role, content) {
    if (!content) return
    messages.value.push({ id: nextId++, role, content })
    scrollMessagesToBottom()
}

async function scrollMessagesToBottom() {
    await nextTick()
    if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight
}

async function scrollVersesToBottom() {
    await nextTick()
    if (verseContainer.value) verseContainer.value.scrollTop = verseContainer.value.scrollHeight
}

async function focusInput() {
    await nextTick()
    chatInput.value?.focus()
}

function wait(milliseconds) {
    return new Promise(resolve => window.setTimeout(resolve, milliseconds))
}
</script>

<style scoped>
.poetry-layout {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(330px, 0.75fr);
    gap: 16px;
}

.poetry-panel,
.chat-panel {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    border: 1px solid rgba(115, 139, 91, 0.18);
    border-radius: var(--radius-lg);
    background: rgba(255, 255, 255, 0.8);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
}

.poetry-panel {
    display: grid;
    grid-template-rows: auto auto auto minmax(0, 1fr) auto;
    background:
        radial-gradient(circle at 12% 8%, rgba(225, 235, 205, 0.7), transparent 34%),
        rgba(255, 255, 252, 0.88);
}

.game-header,
.chat-header {
    padding: 18px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(115, 139, 91, 0.12);
}

.title-wrap {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 13px;
}

.title-wrap p,
.title-wrap h2 {
    margin: 0;
}

.title-wrap p {
    color: #80906c;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: .11em;
}

.title-wrap h2 {
    margin-top: 4px;
    overflow: hidden;
    color: #3f4939;
    font-size: 19px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.back-button,
.restart-button {
    border: 0;
    cursor: pointer;
}

.back-button {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    color: #627054;
    background: rgba(222, 233, 203, .72);
    font-size: 18px;
}

.restart-button {
    padding: 9px 13px;
    border-radius: 12px;
    color: #657353;
    background: rgba(231, 239, 217, .86);
    font-weight: 800;
}

.restart-button:disabled {
    opacity: .55;
    cursor: default;
}

.target-stage {
    margin: 14px 18px 0;
    min-height: 84px;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid rgba(117, 142, 91, .2);
    border-radius: 18px;
    background: linear-gradient(120deg, rgba(237, 244, 223, .96), rgba(255, 252, 242, .92));
}

.target-stage.waiting {
    color: #87917c;
}

.target-stage strong {
    width: 54px;
    height: 54px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    color: #536543;
    background: rgba(255, 255, 255, .78);
    box-shadow: 0 8px 22px rgba(99, 121, 76, .14);
    font-family: "STKaiti", "KaiTi", serif;
    font-size: 36px;
}

.target-stage p {
    margin: 0;
    font-size: 14px;
}

.target-label {
    color: #7d8d69;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: .12em;
}

.status-strip {
    margin: 12px 18px 0;
    padding: 10px 13px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 15px;
    background: rgba(245, 247, 239, .85);
}

.status-strip.urgent {
    background: rgba(255, 238, 229, .9);
}

.turn-copy {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.turn-copy small,
.turn-copy strong {
    display: block;
}

.turn-copy small {
    color: #929b88;
    font-size: 11px;
}

.turn-copy strong {
    margin-top: 2px;
    color: #4e5947;
    font-size: 13px;
}

.turn-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #b7beaF;
}

.turn-dot.user {
    background: #ef9c73;
    box-shadow: 0 0 0 5px rgba(239, 156, 115, .14);
}

.turn-dot.ai {
    background: #8da46f;
    box-shadow: 0 0 0 5px rgba(141, 164, 111, .14);
}

.timer {
    width: 48px;
    height: 48px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: conic-gradient(#8ea772 var(--timer-angle), #e7eadf 0);
    position: relative;
}

.timer::after {
    content: "";
    position: absolute;
    inset: 4px;
    border-radius: inherit;
    background: #fbfcf8;
}

.timer span {
    z-index: 1;
    color: #667456;
    font-size: 10px;
    font-weight: 900;
}

.timer.urgent {
    background: conic-gradient(#e9845e var(--timer-angle), #f2ddd3 0);
}

.timer.complete {
    background: #e8ecdf;
}

.verse-scroll {
    min-height: 0;
    padding: 16px 18px;
    overflow-y: auto;
}

.verse-list {
    display: grid;
    gap: 12px;
}

.verse-card {
    width: 80%;
    box-sizing: border-box;
    padding: 15px 17px 17px;
    border: 1px solid rgba(115, 139, 91, .14);
    border-radius: 18px;
    background: rgba(255, 255, 255, .86);
    box-shadow: 0 8px 22px rgba(92, 111, 73, .07);
}

.verse-card.user {
    margin-left: auto;
    border-color: rgba(231, 159, 121, .22);
    background: rgba(255, 248, 242, .9);
}

.verse-card.ai {
    margin-right: auto;
}

.card-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #98a18e;
    font-size: 10px;
    letter-spacing: .08em;
}

.card-meta em {
    font-style: normal;
    font-weight: 800;
}

.verse-card p {
    margin: 10px 0 0;
    color: #3f483a;
    font-family: "STKaiti", "KaiTi", serif;
    font-size: clamp(18px, 2.1vw, 24px);
    line-height: 1.75;
}

.verse-card mark {
    margin: 0 .03em;
    padding: .03em .14em;
    border-radius: .32em;
    color: #657a51;
    background: rgba(210, 226, 180, .66);
    box-shadow: inset 0 -0.18em rgba(178, 204, 139, .16);
}

.verse-card.newest mark {
    animation: target-bloom .9s ease both;
}

@keyframes target-bloom {
    0% { color: transparent; background: rgba(239, 185, 143, .8); transform: scale(1.18); }
    100% { color: #657a51; background: rgba(210, 226, 180, .66); transform: scale(1); }
}

.cascade-enter-active {
    transition: opacity .4s ease, transform .45s cubic-bezier(.2, .8, .2, 1);
}

.cascade-enter-from {
    opacity: 0;
    transform: translateY(18px);
}

.empty-verses,
.opening-state {
    min-height: 180px;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 12px;
    color: #929d87;
}

.opening-seal {
    width: 52px;
    height: 52px;
    display: grid;
    place-items: center;
    border: 2px solid #98aa7c;
    color: #768b5d;
    font-family: "STKaiti", "KaiTi", serif;
    font-size: 25px;
    transform: rotate(-4deg);
}

.rule-hint {
    padding: 12px 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
    border-top: 1px solid rgba(115, 139, 91, .1);
    color: #929c88;
    font-size: 10px;
}

.rule-hint i {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: #bbc5ae;
}

.chat-panel {
    display: grid;
    grid-template-rows: auto minmax(0, 1fr) auto auto;
}

.chat-header {
    justify-content: flex-start;
    gap: 11px;
}

.chat-header img,
.message > img {
    object-fit: cover;
    border-radius: 50%;
}

.chat-header img {
    width: 42px;
    height: 42px;
}

.chat-header strong,
.chat-header span {
    display: block;
}

.chat-header strong {
    color: #46503f;
    font-size: 14px;
}

.chat-header span {
    margin-top: 3px;
    color: #929b8a;
    font-size: 11px;
}

.chat-header i {
    width: 7px;
    height: 7px;
    display: inline-block;
    border-radius: 50%;
    background: #91a675;
}

.chat-header i.thinking {
    animation: pulse 1.1s ease infinite;
}

@keyframes pulse {
    50% { opacity: .35; transform: scale(.75); }
}

.messages {
    min-height: 0;
    padding: 17px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.message {
    display: flex;
    align-items: flex-start;
    gap: 8px;
}

.message.user {
    justify-content: flex-end;
}

.message > img {
    width: 28px;
    height: 28px;
    flex: 0 0 auto;
}

.message > div {
    max-width: 84%;
}

.speaker {
    margin: 0 5px 4px;
    display: block;
    color: #9ba392;
    font-size: 10px;
}

.message.user .speaker {
    text-align: right;
}

.message p {
    margin: 0;
    padding: 10px 12px;
    border-radius: 6px 16px 16px 16px;
    color: #4e5649;
    background: #f0f3eb;
    font-size: 13px;
    line-height: 1.65;
    white-space: pre-wrap;
}

.message.user p {
    border-radius: 16px 6px 16px 16px;
    background: #fff0e8;
}

.typing {
    display: flex;
    gap: 4px;
}

.typing i {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #8f9b83;
    animation: typing 1s infinite alternate;
}

.typing i:nth-child(2) { animation-delay: .18s; }
.typing i:nth-child(3) { animation-delay: .36s; }

@keyframes typing {
    to { opacity: .25; transform: translateY(-2px); }
}

.chat-input {
    margin: 0 15px;
    padding: 9px;
    border: 1px solid rgba(115, 139, 91, .18);
    border-radius: 16px;
    background: rgba(250, 252, 247, .95);
}

.chat-input textarea {
    width: 100%;
    padding: 5px 6px;
    resize: none;
    border: 0;
    outline: 0;
    color: #46503f;
    background: transparent;
    font: inherit;
    line-height: 1.5;
}

.chat-input textarea::placeholder {
    color: #b6beb0;
    opacity: 1;
}

.input-actions {
    display: flex;
    justify-content: flex-end;
    gap: 7px;
}

.input-actions button {
    padding: 8px 13px;
    border: 0;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 800;
}

.input-actions button:disabled {
    opacity: .42;
    cursor: default;
}

.chat-button {
    color: #79836f;
    background: #edf0e8;
}

.poetry-button {
    color: white;
    background: #849c67;
}

.input-tip {
    margin: 8px 18px 13px;
    color: #a0a798;
    font-size: 10px;
    line-height: 1.45;
}

@media (max-width: 980px) {
    .poetry-layout {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(430px, 1.15fr) minmax(360px, .85fr);
        overflow-y: auto;
    }
}

@media (max-width: 560px) {
    .game-header,
    .chat-header {
        padding: 14px;
    }

    .target-stage,
    .status-strip {
        margin-left: 12px;
        margin-right: 12px;
    }

    .verse-scroll {
        padding: 12px;
    }

    .verse-card.user,
    .verse-card.ai {
        width: 100%;
        margin-left: 0;
        margin-right: 0;
    }
}
</style>
