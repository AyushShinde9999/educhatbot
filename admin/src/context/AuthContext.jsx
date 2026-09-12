import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('kkw_admin_token') || null);
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('kkw_admin_user') || 'null'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      api.get('/api/auth/me')
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('kkw_admin_user', JSON.stringify(res.data));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (username, password) => {
    const response = await api.post('/api/auth/login', { username, password });
    const { access_token, role } = response.data;
    
    setToken(access_token);
    localStorage.setItem('kkw_admin_token', access_token);
    
    const userObj = { username, role };
    setUser(userObj);
    localStorage.setItem('kkw_admin_user', JSON.stringify(userObj));
    return response.data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('kkw_admin_token');
    localStorage.removeItem('kkw_admin_user');
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
