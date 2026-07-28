import { useState } from 'react'
import {
  useOrders,
  useCategories,
  useProducts,
  useCreateCategory,
  useDeleteCategory,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  useUpdateOrderStatus,
} from '../api/hooks'
import apiClient from '../api/client'
import type { Product } from '../api/types'
import { calcDiscountedPrice } from '../api/utils'

type Tab = 'orders' | 'categories' | 'products' | 'deposit'

const STATUS_OPTIONS = ['pending', 'created', 'processing', 'shipped', 'delivered', 'cancelled']

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>('orders')

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Админ-панель</h1>

      <div className="flex gap-1 rounded-lg bg-gray-100 p-1">
        {([['orders', 'Заказы'], ['categories', 'Категории'], ['products', 'Товары'], ['deposit', 'Депозит']] as [Tab, string][]).map(([t, label]) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'orders' && <OrdersTab />}
      {tab === 'categories' && <CategoriesTab />}
      {tab === 'products' && <ProductsTab />}
      {tab === 'deposit' && <DepositTab />}
    </div>
  )
}

// ── Orders Tab ───────────────────────────────────────────
function OrdersTab() {
  const { data: orders, isLoading } = useOrders(100, 0)
  const updateStatus = useUpdateOrderStatus()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [statusValue, setStatusValue] = useState('created')

  const handleUpdate = (idOrder: number) => {
    updateStatus.mutate(
      { id_order: idOrder, status: statusValue },
      { onSuccess: () => setEditingId(null) }
    )
  }

  if (isLoading) return <Loader />

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b bg-gray-50">
          <tr>
            <th className="px-4 py-3 font-medium">ID</th>
            <th className="px-4 py-3 font-medium">Пользователь</th>
            <th className="px-4 py-3 font-medium">Статус</th>
            <th className="px-4 py-3 font-medium">Оплата</th>
            <th className="px-4 py-3 font-medium">Сумма</th>
            <th className="px-4 py-3 font-medium">Дата</th>
            <th className="px-4 py-3 font-medium">Действия</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {orders?.map((order) => (
            <tr key={order.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 font-medium">{order.id}</td>
              <td className="px-4 py-3 font-mono text-xs text-gray-500">{order.uuid_user}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  order.status_order === 'cancelled' ? 'bg-red-100 text-red-800' :
                  order.status_order === 'delivered' ? 'bg-green-100 text-green-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {order.status_order}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`text-xs font-medium ${order.status_payment ? 'text-green-600' : 'text-gray-500'}`}>
                  {order.status_payment ? 'Да' : 'Нет'}
                </span>
              </td>
              <td className="px-4 py-3 font-medium">{order.total_price} ₽</td>
              <td className="px-4 py-3 text-gray-500">
                {new Date(order.created_at).toLocaleString('ru-RU')}
              </td>
              <td className="px-4 py-3">
                {editingId === order.id ? (
                  <div className="flex items-center gap-2">
                    <select
                      value={statusValue}
                      onChange={(e) => setStatusValue(e.target.value)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      {STATUS_OPTIONS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                    <button onClick={() => handleUpdate(order.id)} className="text-xs text-blue-600 hover:underline">OK</button>
                    <button onClick={() => setEditingId(null)} className="text-xs text-gray-500 hover:underline">Отмена</button>
                  </div>
                ) : (
                  <button
                    onClick={() => { setEditingId(order.id); setStatusValue(order.status_order) }}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Изменить статус
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {(!orders || orders.length === 0) && <p className="py-8 text-center text-gray-500">Заказов пока нет</p>}
    </div>
  )
}

// ── Categories Tab ───────────────────────────────────────
function CategoriesTab() {
  const { data: categories, isLoading } = useCategories()
  const createCategory = useCreateCategory()
  const deleteCategory = useDeleteCategory()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await createCategory.mutateAsync({ name, description: description || undefined })
      setName('')
      setDescription('')
    } catch {
      setError('Ошибка создания категории')
    }
  }

  const handleDelete = async (uuid: string) => {
    setError('')
    try {
      await deleteCategory.mutateAsync(uuid)
    } catch {
      setError('Нельзя удалить категорию — в ней есть товары')
    }
  }

  if (isLoading) return <Loader />

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">Новая категория</h2>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Название</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Описание</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={createCategory.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createCategory.isPending ? 'Создание...' : 'Создать'}
          </button>
        </form>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b bg-gray-50 px-4 py-3">
          <h2 className="text-lg font-semibold">Категории ({categories?.length ?? 0})</h2>
        </div>
        {categories && categories.length > 0 ? (
          <ul className="divide-y">
            {categories.map((cat) => (
              <li key={cat.uuid} className="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
                <div>
                  <p className="font-medium text-gray-900">{cat.name}</p>
                  {cat.description && <p className="text-sm text-gray-500">{cat.description}</p>}
                  <p className="mt-0.5 font-mono text-xs text-gray-400">{cat.uuid}</p>
                </div>
                <button
                  onClick={() => handleDelete(cat.uuid)}
                  disabled={deleteCategory.isPending}
                  className="rounded-md px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                >
                  Удалить
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-8 text-center text-gray-500">Категорий пока нет</p>
        )}
      </div>
    </div>
  )
}

// ── Products Tab ─────────────────────────────────────────
function ProductsTab() {
  const { data: categories } = useCategories()
  const { data: products, isLoading } = useProducts({ limit: 100, offset: 0 })
  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()
  const deleteProduct = useDeleteProduct()

  const [editing, setEditing] = useState<string | null>(null)
  const [error, setError] = useState('')

  const emptyForm = {
    name: '',
    description: '',
    price: '',
    sale: '',
    stock: '',
    image_url: '',
    category_id: categories?.[0]?.uuid ?? '',
  }
  const [form, setForm] = useState(emptyForm)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await createProduct.mutateAsync({
        name: form.name,
        description: form.description || undefined,
        price: parseFloat(form.price),
        sale: form.sale ? parseFloat(form.sale) : undefined,
        stock: parseInt(form.stock, 10),
        image_url: form.image_url || undefined,
        category_id: form.category_id,
      })
      setForm(emptyForm)
    } catch {
      setError('Ошибка создания товара')
    }
  }

  const handleUpdate = async (product: Product) => {
    setError('')
    try {
      await updateProduct.mutateAsync({
        uuid: product.uuid,
        name: form.name || product.name,
        description: form.description !== '' ? form.description : product.description ?? undefined,
        price: form.price ? parseFloat(form.price) : parseFloat(product.price),
        sale: form.sale ? parseFloat(form.sale) : product.sale ? parseFloat(product.sale) : undefined,
        stock: form.stock ? parseInt(form.stock, 10) : product.stock,
        image_url: form.image_url !== '' ? form.image_url : product.image_url ?? undefined,
        category_id: form.category_id || product.category_id,
      })
      setEditing(null)
    } catch {
      setError('Ошибка обновления товара')
    }
  }

  const handleDelete = async (uuid: string) => {
    setError('')
    try {
      await deleteProduct.mutateAsync(uuid)
    } catch {
      setError('Ошибка удаления товара')
    }
  }

  const startEdit = (product: Product) => {
    setEditing(product.uuid)
    setForm({
      name: product.name,
      description: product.description ?? '',
      price: product.price,
      sale: product.sale ?? '',
      stock: String(product.stock),
      image_url: product.image_url ?? '',
      category_id: product.category_id,
    })
  }

  if (isLoading) return <Loader />

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">Новый товар</h2>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Input label="Название" required value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
          <Input label="Цена" required type="number" step="0.01" min="0" value={form.price} onChange={(v) => setForm({ ...form, price: v })} />
          <Input label="Скидка (%)" type="number" step="0.01" min="0" max="100" value={form.sale} onChange={(v) => setForm({ ...form, sale: v })} />
          <Input label="Остаток" required type="number" min="0" value={form.stock} onChange={(v) => setForm({ ...form, stock: v })} />
          <Input label="Описание" value={form.description} onChange={(v) => setForm({ ...form, description: v })} />
          <Input label="URL изображения" value={form.image_url} onChange={(v) => setForm({ ...form, image_url: v })} />
          <div>
            <label className="block text-sm font-medium text-gray-700">Категория</label>
            <select
              required
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Выберите</option>
              {categories?.map((cat) => (
                <option key={cat.uuid} value={cat.uuid}>{cat.name}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={createProduct.isPending}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {createProduct.isPending ? 'Создание...' : 'Создать товар'}
            </button>
          </div>
        </form>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm overflow-x-auto">
        <div className="border-b bg-gray-50 px-4 py-3">
          <h2 className="text-lg font-semibold">Товары ({products?.total ?? 0})</h2>
        </div>
        {products && products.items.length > 0 ? (
          <table className="w-full text-left text-sm">
            <thead className="border-b">
              <tr>
                <th className="px-4 py-3 font-medium">Название</th>
                <th className="px-4 py-3 font-medium">Цена</th>
                <th className="px-4 py-3 font-medium">Скидка</th>
                <th className="px-4 py-3 font-medium">Остаток</th>
                <th className="px-4 py-3 font-medium">Категория</th>
                <th className="px-4 py-3 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {products.items.map((product) => (
                <tr key={product.uuid} className="hover:bg-gray-50">
                  {editing === product.uuid ? (
                    <td colSpan={6} className="px-4 py-3">
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <Input label="Название" value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
                        <Input label="Цена" type="number" step="0.01" value={form.price} onChange={(v) => setForm({ ...form, price: v })} />
                        <Input label="Скидка (%)" type="number" step="0.01" value={form.sale} onChange={(v) => setForm({ ...form, sale: v })} />
                        <Input label="Остаток" type="number" value={form.stock} onChange={(v) => setForm({ ...form, stock: v })} />
                        <Input label="Описание" value={form.description} onChange={(v) => setForm({ ...form, description: v })} />
                        <Input label="URL изображения" value={form.image_url} onChange={(v) => setForm({ ...form, image_url: v })} />
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Категория</label>
                          <select
                            value={form.category_id}
                            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                          >
                            {categories?.map((cat) => (
                              <option key={cat.uuid} value={cat.uuid}>{cat.name}</option>
                            ))}
                          </select>
                        </div>
                        <div className="flex items-end gap-2">
                          <button onClick={() => handleUpdate(product)} className="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700">Сохранить</button>
                          <button onClick={() => setEditing(null)} className="rounded bg-gray-200 px-3 py-2 text-sm text-gray-700 hover:bg-gray-300">Отмена</button>
                        </div>
                      </div>
                    </td>
                  ) : (
                    <>
                      <td className="px-4 py-3 font-medium">{product.name}</td>
                      <td className="px-4 py-3">
                        {product.sale ? (
                          <span>
                            <span className="text-red-600 font-medium">{calcDiscountedPrice(product.price, product.sale).toFixed(2)} ₽</span>
                            <span className="ml-1 text-gray-400 line-through text-xs">{product.price} ₽</span>
                            <span className="ml-1 text-xs text-red-500">-{product.sale}%</span>
                          </span>
                        ) : (
                          <span>{product.price} ₽</span>
                        )}
                      </td>
                      <td className="px-4 py-3">{product.sale ? `${product.sale}%` : '—'}</td>
                      <td className="px-4 py-3">{product.stock}</td>
                      <td className="px-4 py-3 text-gray-500">{categories?.find((c) => c.uuid === product.category_id)?.name ?? '—'}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button onClick={() => startEdit(product)} className="text-xs text-blue-600 hover:underline">Редактировать</button>
                          <button onClick={() => handleDelete(product.uuid)} className="text-xs text-red-600 hover:underline">Удалить</button>
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="py-8 text-center text-gray-500">Товаров пока нет</p>
        )}
      </div>
    </div>
  )
}

// ── Deposit Tab ──────────────────────────────────────────
function DepositTab() {
  const [uuidUser, setUuidUser] = useState('')
  const [amount, setAmount] = useState('')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMsg('')
    try {
      await apiClient.post('/payment/deposit', { uuid_user: uuidUser, dep_price: amount })
      setMsg('Депозит выполнен')
      setUuidUser('')
      setAmount('')
    } catch {
      setMsg('Ошибка депозита')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Пополнение кошелька</h2>
      <form onSubmit={handleDeposit} className="space-y-4 max-w-md">
        <Input label="UUID пользователя" required value={uuidUser} onChange={setUuidUser} />
        <Input label="Сумма" required type="number" min="0" step="0.01" value={amount} onChange={setAmount} />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Выполняется...' : 'Пополнить'}
        </button>
        {msg && <p className="text-sm text-gray-600">{msg}</p>}
      </form>
    </div>
  )
}

// ── Shared Components ────────────────────────────────────
function Input({ label, value, onChange, ...props }: {
  label: string
  value: string
  onChange: (v: string) => void
} & Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'>) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <input
        {...props}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  )
}

function Loader() {
  return (
    <div className="flex justify-center py-12">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
    </div>
  )
}
