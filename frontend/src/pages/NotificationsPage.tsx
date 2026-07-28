import { useNotifications, useMarkNotificationsRead } from '../api/hooks'

export default function NotificationsPage() {
  const { data: notifications, isLoading } = useNotifications()
  const markRead = useMarkNotificationsRead()

  const handleMarkAllRead = () => {
    if (!notifications) return
    const unreadIds = notifications.filter((n) => !n.is_read).map((n) => n.uuid)
    if (unreadIds.length > 0) {
      markRead.mutate({ uuid_notifications: unreadIds })
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Уведомления</h1>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            disabled={markRead.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Прочитать все ({unreadCount})
          </button>
        )}
      </div>

      {notifications && notifications.length > 0 ? (
        <div className="space-y-3">
          {notifications.map((notif) => (
            <div
              key={notif.uuid}
              className={`rounded-lg border p-4 shadow-sm ${
                notif.is_read
                  ? 'border-gray-200 bg-white'
                  : 'border-blue-200 bg-blue-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className={`text-sm font-semibold ${notif.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                    {notif.title_notification}
                  </h3>
                  <p className={`mt-1 text-sm ${notif.is_read ? 'text-gray-500' : 'text-gray-700'}`}>
                    {notif.message_notification}
                  </p>
                </div>
                <div className="ml-4 flex flex-col items-end gap-1">
                  {!notif.is_read && (
                    <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
                  )}
                  <span className="text-xs text-gray-400">
                    {new Date(notif.created_at).toLocaleString('ru-RU')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-gray-500">Нет уведомлений</p>
      )}
    </div>
  )
}
