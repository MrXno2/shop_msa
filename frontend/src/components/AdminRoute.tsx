import { Navigate, Outlet } from 'react-router-dom'
import { useMeAdmin } from '../api/hooks'

export default function AdminRoute() {
  const { isLoading, isError } = useMeAdmin()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-900">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  if (isError) {
    return <Navigate to="/admin/login" replace />
  }

  return <Outlet />
}
