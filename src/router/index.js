import { createRouter, createWebHistory } from "vue-router"

import LoginView from "../views/LoginView.vue"
import RegisterView from "../views/RegisterView.vue"

import MainLayout from "../views/MainLayout.vue"
import HomeView from "../views/HomeView.vue"
import ProfileView from "../views/ProfileView.vue"
import PrivateChatView from "../views/PrivateChatView.vue"
import CreateChatView from "../views/CreateChatView.vue"
import PersonaLibraryView from "../views/PersonaLibraryView.vue"

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
router.beforeEach((to, from, next) => {

    const token = localStorage.getItem("token")

    // 不需要登录的页面
    const publicPages = [
        "/login",
        "/register"
    ]

    // 是否是公开页面
    const isPublic = publicPages.includes(to.path)

    // 未登录
    if (!token && !isPublic) {

        next("/login")
        return
    }

    // 已登录还访问 login
    if (token && to.path === "/login") {

        next("/group")
        return
    }

    next()
})

export default router
