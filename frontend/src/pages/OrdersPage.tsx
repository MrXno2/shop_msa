import { useOrders, usePayOrder } from '../api/hooks'

const STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает',
  created: 'Создан',
  processing: 'В обработке',
  shipped: 'Отправлен',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  created: 'bg-blue-100 text-blue-800',
  processing: 'bg-indigo-100 text-indigo-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function OrdersPage() {
  const { data: orders, isLoading } = useOrders()
  const payOrder = usePayOrder()

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Мои заказы</h1>

      {orders && orders.length > 0 ? (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-gray-500">Заказ #{order.id}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
                <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[order.status_order] || 'bg-gray-100 text-gray-800'}`}>
                  {STATUS_LABELS[order.status_order] || order.status_order}
                </span>
              </div>

              <div className="mt-4 space-y-2">
                {order.items.map((item: Record<string, unknown>, idx: number) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span>{String(item.name || item.uuid_product || `Товар ${idx + 1}`)}</span>
                    <span className="text-gray-500">
                      {String(item.price || '')} ₽ × {String(item.count || item.count_product || 1)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-4">
                <span className="font-bold">Итого: {order.total_price} ₽</span>
                <div className="flex items-center gap-3">
                  <span className={`text-sm ${order.status_payment ? 'text-green-600' : 'text-gray-500'}`}>
                    {order.status_payment ? 'Оплачен' : 'Не оплачен'}
                  </span>
                  {!order.status_payment && order.status_order !== 'cancelled' && (
                    <button
                      onClick={() => payOrder.mutate(order.id)}
                      disabled={payOrder.isPending}
                      className="rounded-md bg-green-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      {payOrder.isPending ? 'Оплата...' : 'Оплатить'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-gray-500">У вас пока нет заказов</p>
      )}
    </div>
  )
}
