import { createRouter, createWebHistory } from "vue-router"

import LoginView from "../views/LoginView.vue"
import RegisterView from "../views/RegisterView.vue"

import MainLayout from "../views/MainLayout.vue"

import HomeView from "../views/HomeView.vue"
import ProfileView from "../views/ProfileView.vue"
import PrivateChatView from "../views/PrivateChatView.vue"

import CreateChatView from "../views/CreateChatView.vue"

const routes = [

    {
        path: "/login",
        component: LoginView
    },

    {
        path: "/register",
        component: RegisterView
    },

    {
        path: "/",
        component: MainLayout,

        children: [

            {
                path: "",
                component: HomeView
            },

            {
                path: "profile",
                component: ProfileView
            },

            {
                path: "private",
                component: PrivateChatView
            },

            {
                path: "create",
                component: CreateChatView
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {

    const token = localStorage.getItem("token")

    if (
        to.path !== "/login"
        && to.path !== "/register"
        && !token
    ) {
        next("/login")
    } else {
        next()
    }
})

export default router