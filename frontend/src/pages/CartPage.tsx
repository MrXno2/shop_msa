import { useCart, useRemoveFromCart, useCreateOrder, useBalance } from '../api/hooks'
import { calcDiscountedPrice } from '../api/utils'

export default function CartPage() {
  const { data: cartItems, isLoading } = useCart()
  const { data: balance } = useBalance()
  const removeFromCart = useRemoveFromCart()
  const createOrder = useCreateOrder()

  const totalPrice = cartItems?.reduce((sum, item) => {
    const price = calcDiscountedPrice(item.price, item.sale)
    return sum + price * item.count_product
  }, 0) ?? 0

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Корзина</h1>

      {cartItems && cartItems.length > 0 ? (
        <>
          <div className="space-y-4">
            {cartItems.map((item) => (
              <div
                key={item.uuid}
                className="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
              >
                {item.image_url ? (
                  <img src={item.image_url} alt={item.name} className="h-16 w-16 rounded object-cover" />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded bg-gray-100 text-xs text-gray-400">
                    Нет фото
                  </div>
                )}
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900">{item.name}</h3>
                  <p className="text-sm text-gray-500">
                    {item.sale ? (
                      <>
                        <span className="text-red-600">{calcDiscountedPrice(item.price, item.sale).toFixed(2)} ₽</span>
                        <span className="ml-1 text-gray-400 line-through">{item.price} ₽</span>
                        <span className="ml-1 text-xs text-red-500">-{item.sale}%</span>
                      </>
                    ) : (
                      <>{item.price} ₽</>
                    )}
                    {' '} × {item.count_product} шт.
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">
                    {(calcDiscountedPrice(item.price, item.sale) * item.count_product).toFixed(2)} ₽
                  </p>
                  <button
                    onClick={() => removeFromCart.mutate(item.uuid)}
                    disabled={removeFromCart.isPending}
                    className="mt-1 text-sm text-red-500 hover:text-red-700"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between text-lg font-bold">
              <span>Итого:</span>
              <span>{totalPrice.toFixed(2)} ₽</span>
            </div>
            {balance !== undefined && (
              <p className="mt-1 text-sm text-gray-500">
                Ваш баланс: {balance} ₽
                {parseFloat(balance) < totalPrice && (
                  <span className="ml-2 text-red-500">(недостаточно средств)</span>
                )}
              </p>
            )}
            <button
              onClick={() => createOrder.mutate()}
              disabled={createOrder.isPending}
              className="mt-4 w-full rounded-md bg-blue-600 px-4 py-3 text-white font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {createOrder.isPending ? 'Создание заказа...' : 'Оформить заказ'}
            </button>
          </div>
        </>
      ) : (
        <p className="py-12 text-center text-gray-500">Корзина пуста</p>
      )}
    </div>
  )
}
