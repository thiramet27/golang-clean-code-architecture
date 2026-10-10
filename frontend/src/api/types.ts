export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  created_at: string
  updated_at: string
}

export interface TokenPair {
  access: string
  refresh: string
}

/** Returned by both /users/login and /users/refresh-token. */
export interface Session {
  user: User
  token: TokenPair
}

export interface RegisterInput {
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface AppInfo {
  name: string
  version: string
}

export type FieldType =
  | 'string'
  | 'int'
  | 'double'
  | 'boolean'
  | 'datetime'
  | 'date'
  | 'map'
  | 'array'
  | 'unknown'

export interface SchemaField {
  name: string
  type: FieldType
}

export interface DataSchema {
  type: 'record'
  name: string
  fields: SchemaField[]
}

export type DataRecord = Record<string, unknown>

export interface DataListResponse {
  code: number
  data: DataRecord[]
  page: number
  page_size: number
  total_page: number
  total_data: number
  message: string
  data_schema: DataSchema
}

export interface DataItemResponse {
  code: number
  data: DataRecord
  message: string
  data_schema: DataSchema
}

export interface ErrorBody {
  trace_id?: string
  message?: string
}
