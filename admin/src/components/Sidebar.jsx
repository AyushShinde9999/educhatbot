import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, HelpCircle, Bell, MessageSquareText, ShieldCheck } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { path: '/', label: 'Overview', icon: LayoutDashboard },
    { path: '/documents', label: 'PDF Documents', icon: FileText },
    { path: '/faqs', label: 'Manage FAQs', icon: HelpCircle },
    { path: '/notices', label: 'Manage Notices', icon: Bell },
    { path: '/logs', label: 'Query Logs', icon: MessageSquareText },
    { path: '/audit-logs', label: 'Audit Logs', icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] p-4 flex flex-col justify-between">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Management
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          );
        })}
      </div>

      <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700/60 text-xs">
        <p className="font-semibold text-slate-200">K.K. Wagh Polytechnic</p>
        <p className="text-slate-400 text-[11px] mt-0.5">RAG Engine v2.0 Enterprise</p>
      </div>
    </aside>
  );
};

export default Sidebar;
