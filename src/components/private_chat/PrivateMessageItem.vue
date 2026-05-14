<template>

    <div
        class="message-wrapper"
        :class="{
            mine: isMine
        }"
    >

        <img
            :src="avatar"
            class="avatar"
        />

        <div class="message-content">

            <div class="nickname">
                {{ nickname }}
            </div>

            <div class="bubble">
                {{ message.content }}
            </div>

        </div>

    </div>

</template>

<script setup>
const props = defineProps({

    message: Object,

    isMine: Boolean,

    avatar: String,

    nickname: String,
})
</script>

<style scoped>
.message-wrapper{
    display:flex;
    margin-bottom:20px;
}

.message-wrapper.mine{
    flex-direction:row-reverse;
}

.avatar{
    width:42px;
    height:42px;
    border-radius:50%;
    object-fit:cover;
}

.message-content{
    max-width:60%;
    margin:0 12px;
}

.nickname{
    font-size:13px;
    color:#666;
    margin-bottom:4px;
    text-align:left;
}


.bubble{
    background:white;
    padding:12px;
    border-radius:12px;
    line-height:1.5;
    word-break:break-word;
}

.message-wrapper.mine .bubble{
    background:#95ec69;
}
</style>