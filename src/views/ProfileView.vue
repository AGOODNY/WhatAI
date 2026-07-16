<template>
    <div class="profile-page">
        <section class="profile-card">
            <div class="heading">
                <p>Profile</p>
                <h1>个人中心</h1>
            </div>

            <div class="avatar-section">
                <img :src="avatarPreview" class="avatar" />

                <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    class="file-input"
                    @change="handleFile"
                />

                <button class="change-btn" @click="chooseAvatar">
                    修改头像
                </button>
            </div>

            <div class="info-grid">
                <label class="info-item">
                    <span>用户名</span>
                    <div class="value">{{ username }}</div>
                </label>

                <label class="info-item">
                    <span>昵称</span>
                    <input
                        v-model="nickname"
                        class="nickname-input"
                        placeholder="给自己起个昵称"
                    />
                </label>

                <div class="info-item model-item">
                    <span>聊天模型</span>
                    <p class="model-help">
                        保存后同时应用于群聊、私聊和对话摘要
                    </p>

                    <div class="model-options">
                        <label
                            v-for="model in availableModels"
                            :key="model"
                            class="model-option"
                            :class="{ selected: llmModel === model }"
                        >
                            <input
                                v-model="llmModel"
                                type="radio"
                                name="llm-model"
                                :value="model"
                            />
                            <span>{{ model }}</span>
                        </label>
                    </div>
                </div>
            </div>

            <button class="save-btn" @click="save">
                保存修改
            </button>
        </section>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "@/api/axios"

const username = ref("")
const nickname = ref("nickname")
const avatar = ref(null)
const avatarPreview = ref("/avatars/default.jpg")
const fileInput = ref(null)
const llmModel = ref("deepseek-v3.2")
const availableModels = ref([
    "deepseek-v4-flash",
    "deepseek-v3.2",
    "deepseek-v4-pro",
])

async function fetchProfile() {
    try {
        const res = await axios.get("/api/users/me/")

        username.value = res.data.username
        nickname.value = res.data.nickname || "nickname"
        avatarPreview.value = res.data.avatar_url || "/avatars/default.jpg"
        llmModel.value = res.data.llm_model || "deepseek-v3.2"

        if (Array.isArray(res.data.available_llm_models)) {
            availableModels.value = res.data.available_llm_models
        }
    } catch (err) {
        console.error("获取用户信息失败", err)
    }
}

function chooseAvatar() {
    fileInput.value.click()
}

function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return

    avatar.value = file
    avatarPreview.value = URL.createObjectURL(file)
}

async function save() {
    const formData = new FormData()

    formData.append("nickname", nickname.value)
    formData.append("llm_model", llmModel.value)

    if (avatar.value) {
        formData.append("avatar", avatar.value)
    }

    try {
        const res = await axios.post(
            "/api/users/profile/update/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data"
                }
            }
        )

        if (res.data.avatar_url) {
            avatarPreview.value = res.data.avatar_url
        }

        llmModel.value = res.data.llm_model || llmModel.value

        alert("保存成功")
    } catch (err) {
        console.error(err)
        alert("保存失败")
    }
}

onMounted(fetchProfile)
</script>

<style scoped>
.profile-page {
    width: 100%;
    height: 100%;
    min-width: 0;
    min-height: 0;
    display: grid;
    place-items: center;
    padding: 24px;
    overflow-y: auto;
}

.profile-card {
    width: min(520px, 100%);
    padding: 30px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-soft);
    backdrop-filter: blur(18px);
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.heading {
    text-align: center;
}

.heading p {
    margin: 0 0 6px;
    color: var(--color-muted);
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 0;
    text-transform: uppercase;
}

.heading h1 {
    margin: 0;
    color: #4c4038;
    font-size: 28px;
}

.avatar-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
}

.avatar {
    width: 124px;
    height: 124px;
    border: 5px solid rgba(255, 255, 255, 0.82);
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 16px 34px rgba(164, 109, 78, 0.16);
}

.file-input {
    display: none;
}

.change-btn,
.save-btn {
    border-radius: 16px;
    padding: 12px 18px;
    background: linear-gradient(135deg, var(--color-primary), #f7a575);
    color: white;
    cursor: pointer;
    font-weight: 900;
    box-shadow: 0 14px 26px rgba(249, 140, 83, 0.22);
}

.info-grid {
    display: grid;
    gap: 14px;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.info-item span {
    color: #6f625a;
    font-size: 13px;
    font-weight: 800;
}

.model-item {
    padding-top: 4px;
}

.model-help {
    margin: -2px 0 2px;
    color: var(--color-muted);
    font-size: 12px;
    line-height: 1.5;
}

.model-options {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}

.model-option {
    min-height: 44px;
    padding: 10px 13px;
    border: 1px solid rgba(249, 140, 83, 0.2);
    border-radius: 14px;
    background: rgba(249, 242, 239, 0.62);
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    transition:
        border-color 0.2s ease,
        background-color 0.2s ease,
        box-shadow 0.2s ease;
}

.model-option:hover,
.model-option.selected {
    border-color: rgba(249, 140, 83, 0.52);
    background: rgba(252, 206, 180, 0.28);
    box-shadow: 0 8px 20px rgba(249, 140, 83, 0.1);
}

.model-option input {
    width: 16px;
    height: 16px;
    margin: 0;
    accent-color: var(--color-primary);
}

.model-option span {
    color: #51443c;
    font-size: 13px;
    font-weight: 800;
}

.value,
.nickname-input {
    min-height: 46px;
    border: 1px solid rgba(249, 140, 83, 0.2);
    border-radius: 16px;
    padding: 12px 14px;
    background: rgba(249, 242, 239, 0.76);
    color: var(--color-text);
}

.nickname-input {
    outline: none;
}

.nickname-input:focus {
    border-color: rgba(249, 140, 83, 0.55);
    background: #fff;
    box-shadow: 0 0 0 4px rgba(252, 206, 180, 0.3);
}

.save-btn {
    width: 100%;
    min-height: 48px;
    font-size: 16px;
}
</style>
