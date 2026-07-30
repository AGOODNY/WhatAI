import { defineStore } from "pinia"
import { clearToken } from "../auth"

export const useUserStore = defineStore("user", {

    state: () => ({
        user: null
    }),

    actions: {

        setUser(user) {
            this.user = user
        },

        logout() {
            clearToken()
            this.user = null
        }
    }
})
