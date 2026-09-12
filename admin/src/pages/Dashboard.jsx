import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { FileText, HelpCircle, Bell, MessageSquareText, ShieldCheck, AlertCircle, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/admin/logs/analytics')
      .then(res => setStats(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading analytics data...</div>;
  }

  const statCards = [
    { title: 'PDF Documents', count: stats?.total_documents || 0, icon: FileText, color: 'bg-blue-50 text-blue-600 border-blue-200' },
    { title: 'Active FAQs', count: `${stats?.active_faqs || 0} / ${stats?.total_faqs || 0}`, icon: HelpCircle, color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
    { title: 'Active Notices', count: `${stats?.active_notices || 0} / ${stats?.total_notices || 0}`, icon: Bell, color: 'bg-amber-50 text-amber-600 border-amber-200' },
    { title: 'Total Queries', count: stats?.total_queries || 0, icon: MessageSquareText, color: 'bg-purple-50 text-purple-600 border-purple-200' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Knowledge Base Dashboard</h2>
        <p className="text-xs text-slate-500">Overview of institutional documents, active FAQs, notices, and RAG accuracy</p>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{card.title}</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-1">{card.count}</h3>
              </div>
              <div className={`p-3 rounded-xl border ${card.color}`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Analytics Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-800">RAG Grounded Response Accuracy</h3>
            <TrendingUp className="w-5 h-5 text-emerald-500" />
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs font-medium text-slate-600 mb-1">
                <span>Grounded Answers (Sourced from DB)</span>
                <span>{stats?.grounded_queries || 0} queries</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{
                    width: stats?.total_queries ? `${((stats.grounded_queries / stats.total_queries) * 100).toFixed(0)}%` : '100%'
                  }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium text-slate-600 mb-1">
                <span>Fallback Responses (No Info in Docs)</span>
                <span>{stats?.fallback_queries || 0} queries</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full rounded-full transition-all"
                  style={{
                    width: stats?.total_queries ? `${((stats.fallback_queries / stats.total_queries) * 100).toFixed(0)}%` : '0%'
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-800 mb-2">Quick Ingestion Instructions</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              When you upload a new PDF document, the system automatically extracts text using PyMuPDF, chunks it into 600-character blocks with 100-character overlap, generates 384-dimensional embeddings, and indexes them in ChromaDB.
            </p>
          </div>
          <div className="bg-sky-50 border border-sky-200 text-sky-800 p-3 rounded-lg text-xs mt-4">
            💡 <strong>Pro Tip:</strong> Upload official institute admission brochures, department handbooks, exam rules, and academic calendars for instant AI answering.
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
