import { defineStore } from "pinia"

export const useUserStore = defineStore("user", {

    state: () => ({
        user: null
    }),

    actions: {

        setUser(user) {
            this.user = user
        },

        logout() {
            localStorage.removeItem("token")
            this.user = null
        }
    }
})