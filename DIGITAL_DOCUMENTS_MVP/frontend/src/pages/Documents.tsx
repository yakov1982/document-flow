import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { createDocument, exportDocumentsCsv, listDocuments, type DocumentListItem } from '../api';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  in_review: 'На согласовании',
  approved: 'Согласован',
  rejected: 'Отклонён',
};

const STATUS_CLASS: Record<string, string> = {
  draft: 'status-draft',
  in_review: 'status-review',
  approved: 'status-approved',
  rejected: 'status-rejected',
};

const PAGE_SIZE = 20;

export default function Documents() {
  const [docs, setDocs] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('');
  const [sort, setSort] = useState('created_at_desc');
  const [page, setPage] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [createError, setCreateError] = useState('');
  const [createLoading, setCreateLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listDocuments({
        q: q || undefined,
        status_filter: statusFilter || undefined,
        doc_type_filter: docTypeFilter || undefined,
        sort,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setDocs(list);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [q, statusFilter, docTypeFilter, sort, page]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const title = (form.elements.namedItem('title') as HTMLInputElement).value;
    const doc_type = (form.elements.namedItem('doc_type') as HTMLInputElement).value;
    const reg_number = (form.elements.namedItem('reg_number') as HTMLInputElement).value || undefined;
    const document_date = (form.elements.namedItem('document_date') as HTMLInputElement).value || undefined;
    const counterparty_from = (form.elements.namedItem('counterparty_from') as HTMLInputElement).value || undefined;
    const counterparty_to = (form.elements.namedItem('counterparty_to') as HTMLInputElement).value || undefined;
    const approvers = (form.elements.namedItem('approvers') as HTMLTextAreaElement).value || undefined;
    const fileInput = form.elements.namedItem('file') as HTMLInputElement;
    const file = fileInput?.files?.[0];

    setCreateError('');
    setCreateLoading(true);
    try {
      await createDocument({
        title,
        doc_type,
        reg_number,
        document_date,
        counterparty_from,
        counterparty_to,
        approvers,
        file,
      });
      setShowCreate(false);
      load();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setCreateLoading(false);
    }
  };

  const exportCsv = async () => {
    try {
      await exportDocumentsCsv({ q: q || undefined, status_filter: statusFilter || undefined });
    } catch (err) {
      console.error(err);
    }
  };

  const formatDate = (s: string) => new Date(s).toLocaleString('ru-RU');

  return (
    <div className="page documents-page">
      <header className="page-header">
        <h1>Документы</h1>
        <div className="header-actions">
          <button className="btn" onClick={exportCsv}>Экспорт CSV</button>
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            + Создать документ
          </button>
        </div>
      </header>

      <div className="filters">
        <input
          type="search"
          placeholder="Поиск по названию или номеру…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="search-input"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="status-select"
        >
          <option value="">Все статусы</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={docTypeFilter}
          onChange={(e) => setDocTypeFilter(e.target.value)}
          className="status-select"
        >
          <option value="">Все типы</option>
          <option value="generic">Общий</option>
          <option value="incoming">Входящий</option>
          <option value="outgoing">Исходящий</option>
          <option value="internal">Внутренний</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)} className="status-select">
          <option value="created_at_desc">Дата (новые)</option>
          <option value="created_at_asc">Дата (старые)</option>
          <option value="title_asc">Название А-Я</option>
          <option value="title_desc">Название Я-А</option>
        </select>
      </div>

      {showCreate && (
        <div className="modal-overlay" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Создать документ</h2>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Название *</label>
                <input name="title" required />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Тип</label>
                  <select name="doc_type">
                    <option value="generic">Общий</option>
                    <option value="incoming">Входящий</option>
                    <option value="outgoing">Исходящий</option>
                    <option value="internal">Внутренний</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Рег. номер</label>
                  <input name="reg_number" />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Дата документа</label>
                  <input name="document_date" type="date" />
                </div>
                <div className="form-group">
                  <label>От кого</label>
                  <input name="counterparty_from" placeholder="Контрагент" />
                </div>
                <div className="form-group">
                  <label>Кому</label>
                  <input name="counterparty_to" placeholder="Контрагент" />
                </div>
              </div>
              <div className="form-group">
                <label>Согласующие (через запятую — по шагам; user1|user2 — параллельно)</label>
                <textarea name="approvers" rows={2} placeholder="user1, user2|user3" />
              </div>
              <div className="form-group">
                <label>Файл</label>
                <input name="file" type="file" />
              </div>
              {createError && <div className="form-error">{createError}</div>}
              <div className="modal-actions">
                <button type="button" className="btn" onClick={() => setShowCreate(false)}>
                  Отмена
                </button>
                <button type="submit" className="btn btn-primary" disabled={createLoading}>
                  {createLoading ? 'Создание…' : 'Создать'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Загрузка…</div>
      ) : docs.length === 0 ? (
        <div className="empty">Документов не найдено</div>
      ) : (
        <>
        <div className="documents-table-wrap">
          <table className="documents-table">
            <thead>
              <tr>
                <th>№</th>
                <th>Название</th>
                <th>Тип</th>
                <th>Рег. номер</th>
                <th>Автор</th>
                <th>Статус</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>{d.id}</td>
                  <td>
                    <Link to={`/documents/${d.id}`}>{d.title}</Link>
                  </td>
                  <td>{d.doc_type}</td>
                  <td>{d.reg_number || '—'}</td>
                  <td>{d.created_by_username || '—'}</td>
                  <td>
                    <span className={`badge ${STATUS_CLASS[d.status] || ''}`}>
                      {STATUS_LABELS[d.status] || d.status}
                    </span>
                  </td>
                  <td>{formatDate(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="pagination">
          <button
            type="button"
            className="btn btn-sm"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            ← Назад
          </button>
          <span>Стр. {page + 1}</span>
          <button
            type="button"
            className="btn btn-sm"
            disabled={docs.length < PAGE_SIZE}
            onClick={() => setPage((p) => p + 1)}
          >
            Вперёд →
          </button>
        </div>
        </>
      )}
    </div>
  );
}
