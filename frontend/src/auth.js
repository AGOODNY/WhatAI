const TOKEN_KEY = "token"

let verifiedToken = null

function decodeTokenPayload(token) {
    try {
        const parts = token.split(".")

        if (parts.length !== 3) return null

        const base64 = parts[1]
            .replace(/-/g, "+")
            .replace(/_/g, "/")
            .padEnd(Math.ceil(parts[1].length / 4) * 4, "=")

        return JSON.parse(window.atob(base64))
    } catch {
        return null
    }
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY)
}

export function getActiveToken() {
    const token = getToken()

    if (!token) return null

    const payload = decodeTokenPayload(token)
    const isExpired = !payload?.exp || payload.exp * 1000 <= Date.now()

    if (isExpired) {
        clearToken()
        return null
    }

    return token
}

export function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token)
    verifiedToken = token
}

export function clearToken() {
    localStorage.removeItem(TOKEN_KEY)
    verifiedToken = null
}

export function isTokenVerified(token) {
    return token === verifiedToken
}

export function markTokenVerified(token) {
    if (token === getToken()) {
        verifiedToken = token
    }
}
