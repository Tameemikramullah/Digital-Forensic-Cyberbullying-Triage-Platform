import { NavLink } from 'react-router-dom'
import { FileText, Upload, BarChart3, LayoutDashboard, LogOut, FlaskConical, RefreshCw } from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/evidence', label: 'Evidence Queue', icon: FileText },
  { to: '/evidence/upload', label: 'Upload Evidence', icon: Upload },
  { to: '/model-performance', label: 'Model Performance', icon: BarChart3 },
  { to: '/training-performance', label: 'Training Results', icon: FlaskConical },
  { to: '/reproducibility', label: 'Reproducibility', icon: RefreshCw },
]

export default function Navbar() {
  const handleLogout = () => {
    localStorage.removeItem('access_token')
    window.location.href = '/login'
  }

  return (
    <nav className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <FileText className="text-blue-400" size={24} />
            <span className="font-bold text-lg">Forensic Triage</span>
          </div>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`
                }
              >
                <item.icon size={16} />
                {item.label}
              </NavLink>
            ))}
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </div>

      <div className="md:hidden flex flex-wrap gap-2 px-4 pb-3">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                isActive
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`
            }
          >
            <item.icon size={14} />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}