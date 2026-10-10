import { request } from './client'
import type {
  AppInfo,
  DataItemResponse,
  DataListResponse,
  DataSchema,
  RegisterInput,
  Session,
  User,
} from './types'

export const getAppInfo = () => request<AppInfo>('/')

export const authApi = {
  login: (email: string, password: string) =>
    request<Session>('/users/login', { method: 'POST', body: { email, password } }),

  register: (input: RegisterInput) => request<User>('/users/register', { method: 'POST', body: input }),

  logout: (refreshToken: string) =>
    request<unknown>('/users/logout', { method: 'POST', body: { refresh_token: refreshToken } }),

  profile: () => request<User>('/users/profile', { auth: true }),
}

export interface ListParams {
  page: number
  pageSize: number
  filters: Record<string, string>
}

export const dataApi = {
  describe: (slug: string) => request<DataSchema>(`/data/${encodeURIComponent(slug)}/describe`, { auth: true }),

  list: (slug: string, { page, pageSize, filters }: ListParams) =>
    request<DataListResponse>(`/data/${encodeURIComponent(slug)}/`, {
      auth: true,
      query: { ...filters, _page: page, _pageSize: pageSize },
    }),

  get: (slug: string, id: string) =>
    request<DataItemResponse>(`/data/${encodeURIComponent(slug)}/${encodeURIComponent(id)}`, { auth: true }),
}
