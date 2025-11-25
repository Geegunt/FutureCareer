import type {
  AuthSuccessResponse,
  DashboardSnapshot,
  RequestCodePayload,
  UserProfile,
  VerifyCodePayload,
} from './types'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '') ?? 'http://localhost:8000/api'

const buildUrl = (path: string) => `${API_BASE_URL}${path}`

const defaultHeaders = {
  'Content-Type': 'application/json',
}

export async function requestLoginCode(payload: RequestCodePayload) {
  const response = await fetch(buildUrl('/auth/request-code'), {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error('Не удалось отправить код. Проверь почту и попробуй снова.')
  }
  return response.json()
}

export async function verifyLoginCode(payload: VerifyCodePayload) {
  const response = await fetch(buildUrl('/auth/verify'), {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error('Код недействителен или истёк.')
  }
  return (await response.json()) as AuthSuccessResponse
}

export async function fetchProfile(token: string) {
  const response = await fetch(buildUrl('/users/me'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error('Не удалось получить профиль')
  }
  return (await response.json()) as UserProfile
}

export async function fetchDashboard(token: string) {
  const response = await fetch(buildUrl('/users/me/dashboard'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw new Error('Не удалось загрузить дашборд')
  }
  return (await response.json()) as DashboardSnapshot
}

