import { Link, useLocation } from "react-router-dom";

import { FileUp, Home, MessageSquare, Video } from "lucide-react";

const navItems = [
  { path: "/", label: "Dashboard", icon: Home },
  { path: "/upload", label: "Upload", icon: FileUp },
  { path: "/videos", label: "Videos", icon: Video },
  { path: "/chat", label: "Chat", icon: MessageSquare },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-sentinel-800 border-r border-sentinel-700 flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold text-accent-500">SentinelVision</h1>
          <p className="text-xs text-sentinel-400 mt-1">AI Security Analytics</p>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-accent-600 text-white"
                    : "text-sentinel-300 hover:bg-sentinel-700 hover:text-white"
                }`}
              >
                <Icon size={18} />
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-sentinel-700">
          <p className="text-xs text-sentinel-500">v0.1.0</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}