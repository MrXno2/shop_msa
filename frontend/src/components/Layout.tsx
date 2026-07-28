import { Outlet, Link, useLocation } from 'react-router-dom'
import { useMeAdmin, useUnreadCount } from '../api/hooks'

const userLinks = [
  { to: '/catalog', label: 'Каталог' },
  { to: '/cart', label: 'Корзина' },
  { to: '/orders', label: 'Заказы' },
  { to: '/notifications', label: 'Уведомления' },
]

const adminLinks = [
  { to: '/admin', label: 'Админ-панель' },
]

export default function Layout() {
  const location = useLocation()
  const isAdminPage = location.pathname.startsWith('/admin')
  const { data: adminUuid } = useMeAdmin({ enabled: isAdminPage })
  const { data: unreadCount } = useUnreadCount()
  const links = isAdminPage ? adminLinks : userLinks

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/catalog" className="text-xl font-bold text-blue-600">
                Shop MSA
              </Link>
              <div className="flex gap-4">
                {links.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                      location.pathname === link.to
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    {link.label}
                    {link.to === '/notifications' && unreadCount !== undefined && unreadCount > 0 && (
                      <span className="ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                        {unreadCount > 99 ? '99+' : unreadCount}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              {adminUuid && (
                <span className="text-sm text-gray-500">Admin</span>
              )}
              <Link
                to="/auth"
                className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
                onClick={() => {
                  document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
                  document.cookie = 'admin_access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
                }}
              >
                Выйти
              </Link>
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
