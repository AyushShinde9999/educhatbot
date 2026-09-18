import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, RefreshCw, AlertTriangle, Clock } from 'lucide-react';

const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  // Form State
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Admission');
  const [file, setFile] = useState(null);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/admin/documents');
      setDocuments(res.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || file.name);
    formData.append('category', category);

    try {
      const res = await api.post('/api/admin/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setMessage({ type: 'success', text: res.data.message });
      setTitle('');
      setFile(null);
      fetchDocuments();
    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to upload document' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id, docTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${docTitle}"? This will remove its vectors from ChromaDB.`)) return;

    try {
      await api.delete(`/api/admin/documents/${id}`);
      setMessage({ type: 'success', text: `Document "${docTitle}" deleted successfully.` });
      fetchDocuments();
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to delete document.' });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Document Ingestion Pipeline</h2>
        <p className="text-xs text-slate-500">Atomic PDF upload with SHA-256 deduplication, magic bytes validation, and ChromaDB vector indexing.</p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl border flex items-center gap-2 text-xs ${
          message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Upload Form */}
      <form onSubmit={handleUpload} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide flex items-center gap-2">
          <Upload className="w-4 h-4 text-sky-600" />
          Upload Official Document (PDF - Max 15MB)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Document Title</label>
            <input
              type="text"
              required
              placeholder="e.g. Admission Guidelines 2026"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20"
            >
              <option value="Admission">Admission</option>
              <option value="Academics">Academics</option>
              <option value="Examination">Examination</option>
              <option value="Departments">Departments</option>
              <option value="Facilities">Facilities</option>
              <option value="General">General</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Select PDF File</label>
            <input
              type="file"
              required
              accept=".pdf"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={uploading}
          className="bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-sm flex items-center gap-2 transition-all disabled:opacity-50"
        >
          {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          {uploading ? 'Validating & Indexing Vector Chunks...' : 'Upload & Process Document'}
        </button>
      </form>

      {/* Documents List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <h3 className="text-sm font-bold text-slate-800">Indexed Knowledge Documents</h3>
          <span className="text-xs text-slate-500 font-medium">{documents.length} files total</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">No documents uploaded yet. Upload a PDF above.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="p-3">Title & File</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">File Size</th>
                  <th className="p-3">Chunks</th>
                  <th className="p-3">Uploaded Date</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-700">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80">
                    <td className="p-3">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-5 h-5 text-sky-600 shrink-0" />
                        <div>
                          <p className="font-semibold text-slate-800">{doc.title}</p>
                          <p className="text-[11px] text-slate-400 font-mono">{doc.filename}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-[11px] font-medium border border-slate-200">
                        {doc.category}
                      </span>
                    </td>
                    <td className="p-3">
                      {doc.status === 'ready' && (
                        <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-medium border border-emerald-200">
                          <CheckCircle className="w-3 h-3" /> Ready
                        </span>
                      )}
                      {doc.status === 'processing' && (
                        <span className="inline-flex items-center gap-1 text-sky-700 bg-sky-50 px-2 py-0.5 rounded-full text-[11px] font-medium border border-sky-200 animate-pulse">
                          <Clock className="w-3 h-3" /> Processing
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full text-[11px] font-medium border border-rose-200" title={doc.error_message}>
                          <AlertTriangle className="w-3 h-3" /> Failed
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-slate-500">{(doc.file_size / 1024).toFixed(1)} KB</td>
                    <td className="p-3 font-semibold text-sky-700">{doc.chunk_count} vectors</td>
                    <td className="p-3 text-slate-500">{new Date(doc.upload_date).toLocaleDateString()}</td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.title)}
                        className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete Document"
                      >
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
    </div>
  );
};

export default Documents;
