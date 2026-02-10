import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyAssignments } from '../api';

export default function Assignments() {
  const [items, setItems] = useState<Array<{ id: number; document_id: number; title: string; deadline?: string; status: string }>>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = (await getMyAssignments()) as Array<{ id: number; document_id: number; title: string; deadline?: string; status: string }>;
      setItems(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const formatDate = (s: string) => new Date(s).toLocaleString('ru-RU');

  if (loading) return <div className="page loading">Загрузка…</div>;

  return (
    <div className="page assignments-page">
      <header className="page-header">
        <h1>Мои поручения</h1>
      </header>

      {items.length === 0 ? (
        <div className="empty">Нет поручений</div>
      ) : (
        <ul className="tasks-list">
          {items.map((a) => (
            <li key={a.id}>
              <Link to={`/documents/${a.document_id}`} className="task-link">
                <span className="task-title">{a.title}</span>
                <span className="task-meta">
                  {a.deadline ? formatDate(a.deadline) : '—'} • {a.status}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
