import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { MessageSquareText, ShieldAlert, CheckCircle, Search, PlusCircle } from 'lucide-react';

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [convertingLog, setConvertingLog] = useState(null);

  // Convert to FAQ Form
  const [faqQuestion, setFaqQuestion] = useState('');
  const [faqAnswer, setFaqAnswer] = useState('');
  const [faqCategory, setFaqCategory] = useState('General');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/admin/logs?limit=100');
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const openConvertModal = (log) => {
    setConvertingLog(log);
    setFaqQuestion(log.user_query);
    setFaqAnswer('');
    setFaqCategory('General');
  };

  const handleCreateFaq = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/faqs/admin', {
        question: faqQuestion,
        answer: faqAnswer,
        category: faqCategory,
        is_active: true
      });
      alert('Successfully converted unanswered question into active FAQ!');
      setConvertingLog(null);
    } catch (err) {
      alert('Failed to create FAQ');
    }
  };

  const filteredLogs = logs.filter(log =>
    log.user_query.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.bot_response.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.session_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800">User Query Analytics & Logs</h2>
          <p className="text-xs text-slate-500">Audit user questions, identify fallback responses, and convert unanswered queries directly into FAQs.</p>
        </div>

        {/* Search */}
        <div className="relative w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search queries or responses..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-sky-500/20"
          />
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">Loading query logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">No chat logs found matching your filter.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="p-3">Session & Time</th>
                  <th className="p-3">User Question</th>
                  <th className="p-3">Bot Response</th>
                  <th className="p-3">Grounded Status</th>
                  <th className="p-3 text-right">Quick Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80">
                    <td className="p-3 whitespace-nowrap">
                      <p className="font-mono text-[11px] text-slate-500">{log.session_id.slice(0, 16)}...</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{new Date(log.created_at).toLocaleString()}</p>
                    </td>
                    <td className="p-3 font-semibold text-slate-800 max-w-xs">{log.user_query}</td>
                    <td className="p-3 text-slate-600 max-w-md">
                      <p className="line-clamp-2">{log.bot_response}</p>
                    </td>
                    <td className="p-3 whitespace-nowrap">
                      {log.fallback_used ? (
                        <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full text-[11px] font-medium border border-amber-200">
                          <ShieldAlert className="w-3 h-3" /> Fallback Triggered
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-medium border border-emerald-200">
                          <CheckCircle className="w-3 h-3" /> Grounded Answer
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-right whitespace-nowrap">
                      {log.fallback_used && (
                        <button
                          onClick={() => openConvertModal(log)}
                          className="inline-flex items-center gap-1 bg-amber-100 hover:bg-amber-200 text-amber-900 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors"
                          title="Convert to active FAQ"
                        >
                          <PlusCircle className="w-3.5 h-3.5" /> Convert to FAQ
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Convert to FAQ Modal */}
      {convertingLog && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <PlusCircle className="w-5 h-5 text-amber-600" />
              Convert Unanswered Question into FAQ
            </h3>

            <form onSubmit={handleCreateFaq} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">User Question</label>
                <input
                  type="text"
                  required
                  value={faqQuestion}
                  onChange={(e) => setFaqQuestion(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Official Verified Answer</label>
                <textarea
                  required
                  rows={4}
                  value={faqAnswer}
                  onChange={(e) => setFaqAnswer(e.target.value)}
                  placeholder="Provide official verified answer..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Category</label>
                <input
                  type="text"
                  value={faqCategory}
                  onChange={(e) => setFaqCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setConvertingLog(null)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold"
                >
                  Create Active FAQ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Logs;
