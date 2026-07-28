import { useState } from 'react'
import { useProducts, useCategories, useAddToCart } from '../api/hooks'
import { calcDiscountedPrice } from '../api/utils'
import type { ProductListQuery } from '../api/types'

export default function CatalogPage() {
  const [query, setQuery] = useState<ProductListQuery>({
    sort_by: 'name',
    sort_order: 'asc',
    limit: 20,
    offset: 0,
  })
  const [searchInput, setSearchInput] = useState('')

  const { data: categories } = useCategories()
  const { data: products, isLoading } = useProducts(query)
  const addToCart = useAddToCart()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setQuery({ ...query, search: searchInput || undefined, offset: 0 })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Каталог</h1>

      <div className="flex flex-wrap items-end gap-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            placeholder="Поиск товаров..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Найти
          </button>
        </form>

        <select
          value={query.category_id || ''}
          onChange={(e) => setQuery({ ...query, category_id: e.target.value || undefined, offset: 0 })}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Все категории</option>
          {categories?.map((cat) => (
            <option key={cat.uuid} value={cat.uuid}>{cat.name}</option>
          ))}
        </select>

        <select
          value={`${query.sort_by}-${query.sort_order}`}
          onChange={(e) => {
            const [sort_by, sort_order] = e.target.value.split('-') as [ProductListQuery['sort_by'], ProductListQuery['sort_order']]
            setQuery({ ...query, sort_by, sort_order })
          }}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="name-asc">Название ↑</option>
          <option value="name-desc">Название ↓</option>
          <option value="price-asc">Цена ↑</option>
          <option value="price-desc">Цена ↓</option>
          <option value="stock-asc">Остаток ↑</option>
          <option value="stock-desc">Остаток ↓</option>
        </select>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={query.on_sale || false}
            onChange={(e) => setQuery({ ...query, on_sale: e.target.checked || undefined, offset: 0 })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Со скидкой
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={query.in_stock || false}
            onChange={(e) => setQuery({ ...query, in_stock: e.target.checked || undefined, offset: 0 })}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          В наличии
        </label>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        </div>
      ) : products && products.items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.items.map((product) => (
              <div
                key={product.uuid}
                className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
              >
                {product.image_url ? (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="h-48 w-full object-cover"
                  />
                ) : (
                  <div className="flex h-48 w-full items-center justify-center bg-gray-100 text-gray-400">
                    Нет фото
                  </div>
                )}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900">{product.name}</h3>
                  {product.description && (
                    <p className="mt-1 text-sm text-gray-500 line-clamp-2">{product.description}</p>
                  )}
                  <div className="mt-3 flex items-baseline gap-2">
                    {product.sale ? (
                      <>
                        <span className="text-lg font-bold text-red-600">{calcDiscountedPrice(product.price, product.sale).toFixed(2)} ₽</span>
                        <span className="text-sm text-gray-400 line-through">{product.price} ₽</span>
                        <span className="text-xs text-red-500">-{product.sale}%</span>
                      </>
                    ) : (
                      <span className="text-lg font-bold">{product.price} ₽</span>
                    )}
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className={`text-sm ${product.stock > 0 ? 'text-green-600' : 'text-red-500'}`}>
                      {product.stock > 0 ? `В наличии: ${product.stock} шт.` : 'Нет в наличии'}
                    </span>
                    {product.stock > 0 && (
                      <button
                        onClick={() => addToCart.mutate(product.uuid)}
                        disabled={addToCart.isPending}
                        className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        В корзину
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-center gap-4 pt-4">
            <button
              onClick={() => setQuery({ ...query, offset: Math.max(0, (query.offset || 0) - (query.limit || 20)) })}
              disabled={!query.offset || query.offset === 0}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Назад
            </button>
            <span className="text-sm text-gray-600">
              {query.offset! + 1}–{Math.min(query.offset! + (query.limit || 20), products.total)} из {products.total}
            </span>
            <button
              onClick={() => setQuery({ ...query, offset: (query.offset || 0) + (query.limit || 20) })}
              disabled={(query.offset || 0) + (query.limit || 20) >= products.total}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Далее
            </button>
          </div>
        </>
      ) : (
        <p className="py-12 text-center text-gray-500">Товары не найдены</p>
      )}
    </div>
  )
}
