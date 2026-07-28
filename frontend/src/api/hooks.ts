import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from './client'
import type {
  LoginRequest,
  LoginAdminRequest,
  RegisterRequest,
  Product,
  ProductListQuery,
  PaginatedResponse,
  Category,
  CartItem,
  Order,
  Notification,
  UpdateNotificationRequest,
} from './types'

// ============ Auth ============
export function useLogin() {
  return useMutation({
    mutationFn: (data: LoginRequest) =>
      apiClient.post('/auth/login', data),
  })
}

export function useLoginAdmin() {
  return useMutation({
    mutationFn: (data: LoginAdminRequest) =>
      apiClient.post('/auth/login_admin', data),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) =>
      apiClient.post('/auth/register', data),
  })
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const { data } = await apiClient.get<string>('/auth/me')
      return data
    },
    retry: false,
  })
}

export function useMeAdmin(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['me_admin'],
    queryFn: async () => {
      const { data } = await apiClient.get<string>('/auth/me_admin')
      return data
    },
    retry: false,
    ...options,
  })
}

// ============ Catalog ============
export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const { data } = await apiClient.get<Category[]>('/category/all')
      return data
    },
  })
}

export function useProducts(query: ProductListQuery) {
  return useQuery({
    queryKey: ['products', query],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (query.category_id) params.set('category_id', query.category_id)
      if (query.min_price !== undefined) params.set('min_price', String(query.min_price))
      if (query.max_price !== undefined) params.set('max_price', String(query.max_price))
      if (query.in_stock !== undefined) params.set('in_stock', String(query.in_stock))
      if (query.on_sale !== undefined) params.set('on_sale', String(query.on_sale))
      if (query.search) params.set('search', query.search)
      if (query.sort_by) params.set('sort_by', query.sort_by)
      if (query.sort_order) params.set('sort_order', query.sort_order)
      if (query.limit) params.set('limit', String(query.limit))
      if (query.offset) params.set('offset', String(query.offset))
      const { data } = await apiClient.get<PaginatedResponse<Product>>(`/product/get_list?${params}`)
      return data
    },
  })
}

export function useProduct(uuid: string) {
  return useQuery({
    queryKey: ['product', uuid],
    queryFn: async () => {
      const { data } = await apiClient.get<Product>(`/product/get/${uuid}`)
      return data
    },
    enabled: !!uuid,
  })
}

// ============ Cart ============
export function useCart() {
  return useQuery({
    queryKey: ['cart'],
    queryFn: async () => {
      const { data } = await apiClient.get<CartItem[]>('/cart/get_all')
      return data
    },
  })
}

export function useAddToCart() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (uuidProduct: string) =>
      apiClient.post(`/cart/add/${uuidProduct}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}

export function useRemoveFromCart() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (uuidProduct: string) =>
      apiClient.delete(`/cart/del/${uuidProduct}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}

// ============ Order ============
export function useCreateOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiClient.post('/order/create'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['cart'] })
    },
  })
}

export function usePayOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (idOrder: number) =>
      apiClient.post(`/order/pay_order/${idOrder}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })
}

export function useOrders(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['orders', limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get<Order[]>(`/order/list?limit=${limit}&offset=${offset}`)
      return data
    },
  })
}

// ============ Admin: Category ============
export function useCreateCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      apiClient.post('/category/add', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })
}

export function useDeleteCategory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (uuidCategory: string) =>
      apiClient.delete(`/category/del/${uuidCategory}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] })
    },
  })
}

// ============ Admin: Product ============
export function useCreateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      name: string
      description?: string
      price: number
      sale?: number
      stock: number
      image_url?: string
      category_id: string
    }) => apiClient.post('/product/create', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export function useUpdateProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      uuid: string
      name: string
      description?: string
      price: number
      sale?: number
      stock: number
      image_url?: string
      category_id: string
    }) => apiClient.patch('/product/full_update', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

export function useDeleteProduct() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (uuidProduct: string) =>
      apiClient.delete(`/product/delete/${uuidProduct}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}

// ============ Admin: Deposit ============
export function useDeposit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { uuid_user: string; dep_price: string }) =>
      apiClient.post('/payment/deposit', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['balance'] })
    },
  })
}

// ============ Admin: Order Status ============
export function useUpdateOrderStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { id_order: number; status: string }) =>
      apiClient.patch('/order/update_status_order', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
    },
  })
}

// ============ Payment ============
export function useBalance() {
  return useQuery({
    queryKey: ['balance'],
    queryFn: async () => {
      const { data } = await apiClient.get<string>('/payment/balance')
      return data
    },
  })
}

// ============ Notification ============
export function useNotifications(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ['notifications', limit, offset],
    queryFn: async () => {
      const { data } = await apiClient.get<Notification[]>(`/notification/all?limit=${limit}&offset=${offset}`)
      return data
    },
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ['unread_count'],
    queryFn: async () => {
      const { data } = await apiClient.get<number>('/notification/count')
      return data
    },
  })
}

export function useMarkNotificationsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (req: UpdateNotificationRequest) =>
      apiClient.patch('/notification/update', req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      queryClient.invalidateQueries({ queryKey: ['unread_count'] })
    },
  })
}
