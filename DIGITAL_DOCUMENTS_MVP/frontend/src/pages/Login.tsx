import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthInfo } from '../api';
import { useAuth } from '../AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [ldapEnabled, setLdapEnabled] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    getAuthInfo().then((info) => setLdapEnabled(info.ldap_enabled));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Документооборот</h1>
        <p className="login-subtitle">
          {ldapEnabled ? 'Вход через Active Directory' : 'Войдите в систему'}
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">{ldapEnabled ? 'Логин (учётная запись AD)' : 'Логин'}</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">{ldapEnabled ? 'Пароль AD' : 'Пароль'}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <div className="form-error">{error}</div>}
          <button type="submit" disabled={loading} className="btn btn-primary btn-block">
            {loading ? 'Вход…' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}
