<template>
    <form class="persona-form" @submit.prevent="submit">
        <label>
            <span>人格名称</span>
            <input v-model="form.name" placeholder="例如：温柔的观察者" maxlength="80" />
        </label>

        <label>
            <span>头像地址</span>
            <input v-model="form.avatar" placeholder="可留空，默认使用系统头像" />
        </label>

        <label>
            <span>性格描述</span>
            <textarea v-model="form.description" placeholder="例如：冷静、敏锐，喜欢用轻松的方式拆解问题" />
        </label>

        <label>
            <span>说话风格</span>
            <textarea v-model="form.speaking_style" placeholder="例如：短句、自然、偶尔开玩笑，但不夸张" />
        </label>

        <label>
            <span>补充设定</span>
            <textarea v-model="form.personality_prompt" placeholder="例如：正在扮演一位赛博侦探，会关注细节和动机" />
        </label>

        <div class="actions">
            <button type="submit">{{ submitText }}</button>
            <button v-if="showCancel" type="button" class="ghost" @click="$emit('cancel')">
                取消
            </button>
        </div>
    </form>
</template>

<script setup>
import { reactive, watch } from "vue"

const props = defineProps({
    persona: Object,
    submitText: {
        type: String,
        default: "保存人格",
    },
    showCancel: {
        type: Boolean,
        default: true,
    },
})

const emit = defineEmits(["submit", "cancel"])

const form = reactive({
    name: "",
    avatar: "",
    description: "",
    speaking_style: "",
    personality_prompt: "",
})

function fillForm(persona) {
    form.name = persona?.name || ""
    form.avatar = persona?.avatar || ""
    form.description = persona?.description || ""
    form.speaking_style = persona?.speaking_style || ""
    form.personality_prompt = persona?.personality_prompt || ""
}

watch(
    () => props.persona,
    fillForm,
    { immediate: true }
)

function submit() {
    if (!form.name.trim()) {
        alert("请填写人格名称")
        return
    }

    emit("submit", { ...form })
}
</script>

<style scoped>
.persona-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

label {
    display: flex;
    flex-direction: column;
    gap: 7px;
}

span {
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
    min-height: 78px;
    resize: vertical;
}

.actions {
    display: flex;
    gap: 10px;
    padding-top: 2px;
}

button {
    border-radius: 16px;
    padding: 12px 16px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: white;
    cursor: pointer;
    font-weight: 800;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.2);
}

.ghost {
    background: rgba(249, 242, 239, 0.9);
    color: var(--color-text);
    box-shadow: none;
}
</style>
