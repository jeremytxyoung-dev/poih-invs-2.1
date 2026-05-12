import { BarChart3, ClipboardList, LayoutDashboard, Package, Upload } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const tabs = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/count', label: 'Count', icon: ClipboardList },
  { to: '/variance', label: 'Variance', icon: BarChart3 },
  { to: '/pos-import', label: 'POS', icon: Upload },
  { to: '/products', label: 'Products', icon: Package },
]

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <main className="pb-24">{children}</main>
      <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-700 bg-gray-800 px-2 py-2">
        <div className="mx-auto flex max-w-md items-center justify-around">
          {tabs.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-item ${isActive ? 'text-blue-400' : 'text-gray-400'}`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
