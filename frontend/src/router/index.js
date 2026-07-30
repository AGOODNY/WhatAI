import { createRouter, createWebHistory } from "vue-router"

import LoginView from "../views/LoginView.vue"
import RegisterView from "../views/RegisterView.vue"

import MainLayout from "../views/MainLayout.vue"
import HomeView from "../views/HomeView.vue"
import ProfileView from "../views/ProfileView.vue"
import PrivateChatView from "../views/PrivateChatView.vue"
import CreateChatView from "../views/CreateChatView.vue"
import PersonaLibraryView from "../views/PersonaLibraryView.vue"
import PlayView from "../views/PlayView.vue"
import axios from "../api/axios"
import {
    getActiveToken,
    isTokenVerified,
    markTokenVerified
} from "../auth"

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
                redirect: "/group"
            },

            {
                path: "/group",
                component: HomeView
            },

            {
                path: "/profile",
                component: ProfileView
            },

            {
                path: "/private",
                component: PrivateChatView
            },

            {
                path: "/create",
                component: CreateChatView
            },

            {
                path: "/personas",
                component: PersonaLibraryView
            },

            {
                path: "/play",
                component: PlayView
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

/**
 * 路由守卫
 */
router.beforeEach(async to => {

    const token = getActiveToken()

    // 不需要登录的页面
    const publicPages = [
        "/login",
        "/register"
    ]

    // 是否是公开页面
    const isPublic = publicPages.includes(to.path)

    // 未登录
    if (!token && !isPublic) {
        return {
            path: "/login",
            query: { redirect: to.fullPath }
        }
    }

    // 已登录还访问 login
    if (token && to.path === "/login") {
        return "/group"
    }

    if (token && !isPublic && !isTokenVerified(token)) {
        try {
            await axios.get("/api/users/me/")
            markTokenVerified(token)
        } catch (error) {
            if (error.response?.status === 401) {
                return {
                    path: "/login",
                    query: { redirect: to.fullPath }
                }
            }

            // 鉴权服务暂时不可用时不误删仍在有效期内的登录态。
        }
    }

    return true
})

export default router
