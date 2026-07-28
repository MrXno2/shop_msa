import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useMe, useMeAdmin, useUnreadCount, useBalance } from '../api/hooks'

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
  const navigate = useNavigate()
  const isAdminPage = location.pathname.startsWith('/admin')
  const { data: userUuid } = useMe({ enabled: !isAdminPage })
  const { data: adminUuid } = useMeAdmin({ enabled: isAdminPage })
  const { data: unreadCount } = useUnreadCount()
  const { data: balance } = useBalance()
  const links = isAdminPage ? adminLinks : userLinks
  const [copied, setCopied] = useState(false)

  const handleLogout = () => {
    document.cookie = 'access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
    document.cookie = 'admin_access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;'
    navigate(isAdminPage ? '/admin/login' : '/auth')
  }

  return (
    <div className="min-h-screen">
      <nav className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to={isAdminPage ? '/admin' : '/catalog'} className="text-xl font-bold text-blue-600">
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
              {!isAdminPage && balance !== undefined && (
                <span className="rounded-md bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700">
                  {Number(balance).toLocaleString('ru-RU')} ₽
                </span>
              )}
              {userUuid && (
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(userUuid)
                    setCopied(true)
                    setTimeout(() => setCopied(false), 1500)
                  }}
                  className="rounded-md px-3 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-700"
                  title={copied ? 'Скопировано!' : userUuid}
                >
                  {copied ? 'Скопировано!' : 'UUID'}
                </button>
              )}
              <button
                onClick={handleLogout}
                className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                Выйти
              </button>
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
