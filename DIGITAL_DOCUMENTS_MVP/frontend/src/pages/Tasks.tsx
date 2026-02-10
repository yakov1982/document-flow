import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyTasks, type TaskItem } from '../api';

export default function Tasks() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await getMyTasks();
      setTasks(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <div className="page loading">Загрузка…</div>;

  return (
    <div className="page tasks-page">
      <header className="page-header">
        <h1>Мои задачи</h1>
      </header>

      {tasks.length === 0 ? (
        <div className="empty">Нет задач на согласование</div>
      ) : (
        <ul className="tasks-list">
          {tasks.map((t) => (
            <li key={t.step_id}>
              <Link to={`/documents/${t.document_id}`} className="task-link">
                <span className="task-title">{t.title}</span>
                <span className="task-meta">Шаг {t.step_order}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
