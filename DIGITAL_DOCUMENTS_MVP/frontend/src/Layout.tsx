import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      <nav className="sidebar">
        <div className="sidebar-brand">Документооборот</div>
        <ul className="nav-links">
          <li><NavLink to="/" end>Документы</NavLink></li>
          <li><NavLink to="/tasks">Мои задачи</NavLink></li>
          <li><NavLink to="/assignments">Мои поручения</NavLink></li>
        </ul>
        <div className="sidebar-footer">
          <span className="user-name">{user?.username}</span>
          <button type="button" className="btn btn-sm" onClick={logout}>
            Выйти
          </button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
