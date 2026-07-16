import axios from "axios"
import { clearToken, getActiveToken } from "../auth"

const instance = axios.create({
    baseURL: "/"
})

instance.interceptors.request.use(config => {

    const token = getActiveToken()

    if (token) {
        config.headers.Authorization =
            `Bearer ${token}`
    }

    return config
})

let redirectingToLogin = false

instance.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401) {
            clearToken()

            if (window.location.pathname !== "/login" && !redirectingToLogin) {
                redirectingToLogin = true

                const currentPath =
                    `${window.location.pathname}${window.location.search}${window.location.hash}`
                const loginUrl = new URL("/login", window.location.origin)

                loginUrl.searchParams.set("redirect", currentPath)
                window.location.replace(`${loginUrl.pathname}${loginUrl.search}`)
            }
        }

        return Promise.reject(error)
    }
)

export default instance
