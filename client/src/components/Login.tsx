// src/components/Login.tsx
import React, { useState } from 'react';
import '../styles/Login.css';
type AuthMode = 'login' | 'register';
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface LoginProps {
  onLogin?: (user?: any) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const resetMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();

    if (!email || !password || (mode === 'register' && !name)) {
      setError('Vui lòng điền đầy đủ thông tin');
      return;
    }

    setLoading(true);
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const payload: any = { email, password };
      if (mode === 'register') {
        payload.name = name;
        payload.type = 1;
      }

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        const message = data.detail || data.message || 'Lỗi khi kết nối tới server';
        setError(String(message));
        return;
      }

      if (data && (data.success === false || data.access_token === undefined)) {
        setError(data.message || JSON.stringify(data));
        return;
      }

      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
        if (data.user) localStorage.setItem('user', JSON.stringify(data.user));
        setSuccess(mode === 'login' ? 'Đăng nhập thành công' : 'Tạo tài khoản thành công');
        setPassword('');
        if (mode === 'register') setName('');
        try { onLogin && onLogin(data.user); } catch (e) { /* ignore */ }
      } else {
        setError('Phản hồi không hợp lệ từ server');
      }
    } catch (err: any) {
      setError(err?.message || 'Lỗi không xác định');
    } finally {
      setLoading(false);
    }
  };

  // render
  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="24" height="24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 11c0-1.657 1.343-3 3-3s3 1.343 3 3v2a3 3 0 01-3 3h-6a3 3 0 01-3-3v-2c0-1.657 1.343-3 3-3s3 1.343 3 3z" />
            </svg>
          </div>
          <div>
            <div className="login-header-title">Bảng điều khiển IoT</div>
            <div className="login-header-sub">Quản lý thiết bị và truy cập hệ thống</div>
          </div>
        </div>

        <div style={{ padding: '0 0.25rem 1rem 0.25rem' }}>
          <h2 style={{ fontSize: '1.75rem', margin: '0 0 4px 0' }}>{mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}</h2>
          <p className="lead" style={{ marginBottom: '0.75rem' }}>{mode === 'login' ? 'Nhập thông tin tài khoản của bạn' : 'Tạo tài khoản mới để bắt đầu'}</p>
        </div>

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        <form onSubmit={handleSubmit} className="login-form" style={{ marginTop: 6 }}>
          {mode === 'register' && (
            <div className="form-group">
              <label>Họ tên</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Tên hiển thị" disabled={loading} />
            </div>
          )}

          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" disabled={loading} />
          </div>

          <div className="form-group">
            <label>Mật khẩu</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mật khẩu" disabled={loading} />
          </div>

          <div className="form-actions">
            <button type="submit" disabled={loading} className="btn primary">
              {loading ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
            </button>

            <button type="button" onClick={() => { resetMessages(); setMode(mode === 'login' ? 'register' : 'login'); }} disabled={loading} className="btn link">
              {mode === 'login' ? 'Chưa có tài khoản? Tạo mới' : 'Đã có tài khoản? Đăng nhập'}
            </button>
          </div>

          <div className="login-note"></div>
        </form>

        <div className="login-footer">Bản quyền © {new Date().getFullYear()} — Hệ thống IoT</div>
      </div>
    </div>
  );
};

export default Login;
