import { Navigate, Outlet } from 'react-router-dom'
import { useMe } from '../api/hooks'

export default function ProtectedRoute() {
  const { isLoading, isError } = useMe()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
      </div>
    )
  }

  if (isError) {
    return <Navigate to="/auth" replace />
  }

  return <Outlet />
}
