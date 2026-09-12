import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon, ShieldCheck } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6 sticky top-0 z-30 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="bg-brand-800 text-white p-2 rounded-lg font-bold text-sm">
          KKW
        </div>
        <div>
          <h1 className="text-base font-semibold text-slate-800">K.K. Wagh Polytechnic Admin Portal</h1>
          <p className="text-xs text-slate-500">AI Institutional Knowledge Management System</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-full text-xs text-slate-700">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span className="font-medium">{user?.username || 'Admin'}</span>
          <span className="bg-slate-200 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold text-slate-600">
            {user?.role || 'Admin'}
          </span>
        </div>

        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 px-3 py-1.5 rounded-lg border border-rose-200 transition-colors font-medium"
          title="Sign out"
        >
          <LogOut className="w-3.5 h-3.5" />
          Logout
        </button>
      </div>
    </header>
  );
};

export default Navbar;
