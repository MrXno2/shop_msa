export interface LoginRequest {
  number: string
  password: string
}

export interface LoginAdminRequest {
  login: string
  password: string
}

export interface RegisterRequest {
  number: string
  password1: string
  password2: string
  email: string
  country: string
  city: string
  address: string
}

export interface Category {
  uuid: string
  name: string
  description: string | null
}

export interface Product {
  uuid: string
  name: string
  description: string | null
  price: string
  sale: string | null
  stock: number
  image_url: string | null
  category_id: string
}

export interface ProductListQuery {
  category_id?: string
  min_price?: number
  max_price?: number
  in_stock?: boolean
  on_sale?: boolean
  search?: string
  sort_by?: 'name' | 'price' | 'stock'
  sort_order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface CartItem {
  uuid: string
  name: string
  price: string
  sale: string | null
  image_url: string | null
  count_product: number
}

export interface Order {
  id: number
  uuid_user: string
  status_order: string
  status_payment: boolean
  created_at: string
  total_price: string
  items: Record<string, unknown>[]
}

export interface Notification {
  uuid: string
  uuid_user: string
  title_notification: string
  message_notification: string
  created_at: string
  is_read: boolean
}

export interface UpdateNotificationRequest {
  uuid_notifications: string[]
}

export interface DepositRequest {
  uuid_user: string
  dep_price: string
}
