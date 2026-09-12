import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Bell, Plus, Edit2, Trash2, Calendar, CheckCircle, XCircle } from 'lucide-react';

const Notices = () => {
  const [notices, setNotices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingNotice, setEditingNotice] = useState(null);

  // Form State
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('Notice');
  const [expiryDate, setExpiryDate] = useState('');
  const [isActive, setIsActive] = useState(true);

  const fetchNotices = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/notices/admin/all');
      setNotices(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  const openCreateModal = () => {
    setEditingNotice(null);
    setTitle('');
    setContent('');
    setCategory('Notice');
    setExpiryDate('');
    setIsActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (notice) => {
    setEditingNotice(notice);
    setTitle(notice.title);
    setContent(notice.content);
    setCategory(notice.category);
    setExpiryDate(notice.expiry_date ? new Date(notice.expiry_date).toISOString().slice(0, 10) : '');
    setIsActive(notice.is_active);
    setIsModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const payload = {
      title,
      content,
      category,
      expiry_date: expiryDate ? new Date(expiryDate).toISOString() : null,
      is_active: isActive
    };

    try {
      if (editingNotice) {
        await api.put(`/api/notices/admin/${editingNotice.id}`, payload);
      } else {
        await api.post('/api/notices/admin', payload);
      }
      setIsModalOpen(false);
      fetchNotices();
    } catch (err) {
      alert('Failed to save notice');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this Notice?')) return;
    try {
      await api.delete(`/api/notices/admin/${id}`);
      fetchNotices();
    } catch (err) {
      alert('Failed to delete notice');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Notice Management</h2>
          <p className="text-xs text-slate-500">Publish time-sensitive institutional notices with optional expiry dates.</p>
        </div>
        <button
          onClick={openCreateModal}
          className="bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm flex items-center gap-1.5 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create New Notice
        </button>
      </div>

      {/* Notices Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">Loading notices...</div>
        ) : notices.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">No notices created yet. Click "Create New Notice" above.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="p-3">Notice Title</th>
                  <th className="p-3">Content</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Expiry Date</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {notices.map((notice) => (
                  <tr key={notice.id} className="hover:bg-slate-50/80">
                    <td className="p-3 font-semibold text-slate-800 max-w-xs">{notice.title}</td>
                    <td className="p-3 text-slate-600 max-w-md truncate">{notice.content}</td>
                    <td className="p-3">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-[11px] font-medium border border-slate-200">
                        {notice.category}
                      </span>
                    </td>
                    <td className="p-3 text-slate-500 flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      {notice.expiry_date ? new Date(notice.expiry_date).toLocaleDateString() : 'No expiry'}
                    </td>
                    <td className="p-3">
                      {notice.is_active ? (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-medium">
                          <CheckCircle className="w-3 h-3" /> Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px] font-medium">
                          <XCircle className="w-3 h-3" /> Inactive
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-right space-x-1">
                      <button onClick={() => openEditModal(notice)} className="p-1.5 text-sky-600 hover:bg-sky-50 rounded-lg">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(notice.id)} className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-slate-800">
              {editingNotice ? 'Edit Notice' : 'Create New Notice'}
            </h3>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. MSBTE Winter Examination Schedule Released"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Notice Content</label>
                <textarea
                  required
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Detailed notice body..."
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Expiry Date (Optional)</label>
                  <input
                    type="date"
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex items-center pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                  <input
                    type="checkbox"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="rounded text-sky-600 focus:ring-sky-500"
                  />
                  Active Notice
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold"
                >
                  Save Notice
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Notices;
