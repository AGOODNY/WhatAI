<template>

    <div class="select-page">

        <div
            v-for="persona in personas"
            :key="persona.id"
            class="card"
            @click="selectCharacter(persona.id)"
        >

            <img
                :src="persona.avatar"
                class="avatar"
            />

            <div class="name">
                {{ persona.name }}
            </div>

        </div>

    </div>

</template>

<script setup>
import axios from "../../api/axios"

import { PERSONA_MAP } from "../../constants/personas"

const emit = defineEmits([
    "room-created"
])

const personas = Object.values(
    PERSONA_MAP
)

async function selectCharacter(ai_role){

    try{

        const res = await axios.post(
            "/api/private-chat/rooms/create/",
            {
                ai_role
            }
        )

        emit(
            "room-created",
            res.data
        )

    }catch(err){

        console.error(err)
    }
}
</script>

<style scoped>
.select-page{
    flex:1;
    display:flex;
    justify-content:center;
    align-items:center;
    gap:40px;
    background:#f5f5f5;
}

.card{
    width:180px;
    height:240px;

    background:white;

    border-radius:16px;

    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;

    cursor:pointer;

    transition:0.2s;
}

.card:hover{
    transform:translateY(-5px);
}

.avatar{
    width:120px;
    height:120px;

    border-radius:50%;

    object-fit:cover;
}

.name{
    margin-top:20px;
    font-size:20px;
    font-weight:bold;
}
</style>