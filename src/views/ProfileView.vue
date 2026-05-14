<template>
    <div class="profile-page">
        <div class="profile-card">

            <h1 class="title">
                个人中心
            </h1>

            <div class="avatar-section">

                <img
                    :src="avatarPreview"
                    class="avatar"
                />

                <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    style="display:none"
                    @change="handleFile"
                />

                <button
                    class="change-btn"
                    @click="chooseAvatar"
                >
                    修改头像
                </button>

            </div>

            <div class="info-item">
                <div class="label">
                    用户名
                </div>

                <div class="value">
                    {{ username }}
                </div>
            </div>

            <div class="info-item">

                <div class="label">
                    昵称
                </div>

                <input
                    v-model="nickname"
                    class="nickname-input"
                />

            </div>

            <button
                class="save-btn"
                @click="save"
            >
                保存修改
            </button>

        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "@/api/axios"

const username = ref("")
const nickname = ref("nickname")

const avatar = ref(null)

const avatarPreview = ref(
    "/avatars/default.jpg"
)

const fileInput = ref(null)

async function fetchProfile() {

    try {

        const res = await axios.get(
            "/api/users/me/"
        )

        username.value = res.data.username

        nickname.value =
            res.data.nickname || "nickname"

        if (res.data.avatar_url) {

            avatarPreview.value =
                res.data.avatar_url

        } else {

            avatarPreview.value =
                "/avatars/default.jpg"
        }

    } catch (err) {

        console.error(
            "获取用户信息失败",
            err
        )
    }
}

function chooseAvatar() {
    fileInput.value.click()
}

function handleFile(e) {

    const file = e.target.files[0]

    if (!file) return

    avatar.value = file

    avatarPreview.value =
        URL.createObjectURL(file)
}

async function save() {

    const formData = new FormData()

    formData.append(
        "nickname",
        nickname.value
    )

    if (avatar.value) {

        formData.append(
            "avatar",
            avatar.value
        )
    }

    try {

        const res = await axios.post(
            "/api/users/profile/update/",
            formData,
            {
                headers: {
                    "Content-Type":
                        "multipart/form-data"
                }
            }
        )

        if (res.data.avatar_url) {

            avatarPreview.value =
                res.data.avatar_url
        }

        alert("保存成功")

    } catch (err) {

        console.error(err)

        alert("保存失败")
    }
}

onMounted(() => {
    fetchProfile()
})
</script>

<style scoped>
.profile-page{
    width:100%;
    height:100%;
    background:#f5f6fa;
    display:flex;
    justify-content:center;
    align-items:center;
}

.profile-card{
    width:420px;
    background:white;
    border-radius:20px;
    padding:40px;
    box-shadow:0 4px 20px rgba(0,0,0,0.08);
    display:flex;
    flex-direction:column;
    gap:25px;
}

.title{
    text-align:center;
    margin:0;
}

.avatar-section{
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:15px;
}

.avatar{
    width:120px;
    height:120px;
    border-radius:50%;
    object-fit:cover;
    border:4px solid #eee;
}

.change-btn{
    padding:10px 20px;
    border:none;
    border-radius:10px;
    background:#5865f2;
    color:white;
    cursor:pointer;
}

.change-btn:hover{
    background:#4752c4;
}

.info-item{
    display:flex;
    flex-direction:column;
    gap:8px;
}

.label{
    font-size:14px;
    color:#666;
}

.value{
    padding:12px;
    background:#f0f2f5;
    border-radius:10px;
}

.nickname-input{
    padding:12px;
    border:1px solid #ddd;
    border-radius:10px;
    outline:none;
}

.nickname-input:focus{
    border-color:#5865f2;
}

.save-btn{
    margin-top:10px;
    padding:14px;
    border:none;
    border-radius:12px;
    background:#3ba55d;
    color:white;
    font-size:16px;
    cursor:pointer;
}

.save-btn:hover{
    background:#2d7d46;
}
</style>