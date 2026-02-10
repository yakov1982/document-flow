import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  approveDocument,
  createAssignment,
  delegateStep,
  downloadSignature,
  downloadVersion,
  getAuditLog,
  getDocument,
  getUsers,
  rejectDocument,
  signDocument,
  uploadVersion,
  type AuditLogItem,
  type DocumentOut,
  type User,
} from '../api';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  in_review: 'На согласовании',
  approved: 'Согласован',
  rejected: 'Отклонён',
};

const STEP_STATE_LABELS: Record<string, string> = {
  pending: 'Ожидает',
  approved: 'Согласован',
  rejected: 'Отклонён',
  skipped: 'Пропущен',
};

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const [doc, setDoc] = useState<DocumentOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [comment, setComment] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [signCertSubject, setSignCertSubject] = useState('');
  const [signCertThumbprint, setSignCertThumbprint] = useState('');
  const [signatureFile, setSignatureFile] = useState<File | null>(null);
  const [showRejectConfirm, setShowRejectConfirm] = useState(false);
  const [auditLog, setAuditLog] = useState<AuditLogItem[]>([]);
  const [showAudit, setShowAudit] = useState(false);
  const [delegateTo, setDelegateTo] = useState('');
  const [delegateStepId, setDelegateStepId] = useState<number | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [assignTitle, setAssignTitle] = useState('');
  const [assignAssignee, setAssignAssignee] = useState('');
  const [assignDeadline, setAssignDeadline] = useState('');

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const d = await getDocument(Number(id));
      setDoc(d);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleApprove = async () => {
    if (!doc) return;
    setActionLoading(true);
    try {
      const updated = await approveDocument(doc.id, comment || undefined);
      setDoc(updated);
      setComment('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!doc) return;
    setActionLoading(true);
    try {
      const updated = await rejectDocument(doc.id, comment || undefined);
      setDoc(updated);
      setComment('');
      setShowRejectConfirm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelegate = async () => {
    if (!doc || !delegateStepId || !delegateTo) return;
    setActionLoading(true);
    try {
      const updated = await delegateStep(doc.id, delegateStepId, delegateTo);
      setDoc(updated);
      setDelegateTo('');
      setDelegateStepId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка делегирования');
    } finally {
      setActionLoading(false);
    }
  };

  const loadAudit = async () => {
    if (!id) return;
    const log = await getAuditLog(Number(id));
    setAuditLog(log);
    setShowAudit(true);
  };

  const handleCreateAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doc || !assignTitle || !assignAssignee) return;
    setActionLoading(true);
    try {
      await createAssignment({
        document_id: doc.id,
        assignee_username: assignAssignee,
        title: assignTitle,
        deadline: assignDeadline || undefined,
      });
      setAssignTitle('');
      setAssignAssignee('');
      setAssignDeadline('');
      const updated = await getDocument(doc.id);
      setDoc(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка');
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    getUsers().then(setUsers);
  }, []);

  const handleUploadVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doc || !uploadFile) return;
    setActionLoading(true);
    try {
      const updated = await uploadVersion(doc.id, uploadFile);
      setDoc(updated);
      setUploadFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doc) return;
    setActionLoading(true);
    try {
      const updated = await signDocument(doc.id, {
        certSubject: signCertSubject || undefined,
        certThumbprint: signCertThumbprint || undefined,
        signatureFile: signatureFile || undefined,
      });
      setDoc(updated);
      setSignCertSubject('');
      setSignCertThumbprint('');
      setSignatureFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка подписания');
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (s: string) => new Date(s).toLocaleString('ru-RU');

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) return <div className="page loading">Загрузка…</div>;
  if (error && !doc) return <div className="page error">{error}</div>;
  if (!doc) return null;

  const sortedSteps = [...doc.steps].sort((a, b) => a.step_order - b.step_order);

  return (
    <div className="page document-detail">
      <header className="page-header">
        <h1>{doc.title}</h1>
        <span className={`badge badge-lg ${doc.status}`}>{STATUS_LABELS[doc.status] || doc.status}</span>
      </header>

      {error && <div className="form-error">{error}</div>}

      <div className="detail-grid">
        <section className="detail-card">
          <h2>Карточка</h2>
          <dl>
            <dt>Тип</dt>
            <dd>{doc.doc_type}</dd>
            <dt>Рег. номер</dt>
            <dd>{doc.reg_number || '—'}</dd>
            <dt>Дата документа</dt>
            <dd>{doc.document_date ? formatDate(doc.document_date) : '—'}</dd>
            <dt>От кого</dt>
            <dd>{doc.counterparty_from || '—'}</dd>
            <dt>Кому</dt>
            <dd>{doc.counterparty_to || '—'}</dd>
            <dt>Создан</dt>
            <dd>{formatDate(doc.created_at)}</dd>
          </dl>
          <button type="button" className="btn btn-sm" onClick={loadAudit}>Журнал аудита</button>
        </section>

        <section className="detail-card">
          <h2>Поручения</h2>
          {(doc.assignments ?? []).length > 0 ? (
            <ul className="assignments-list">
              {(doc.assignments as Array<{ id: number; title: string; deadline?: string; status: string }>).map((a) => (
                <li key={a.id}>{a.title} — {a.deadline ? formatDate(a.deadline) : '—'} ({a.status})</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Нет поручений</p>
          )}
          <form onSubmit={handleCreateAssignment} className="assign-form">
            <input value={assignTitle} onChange={(e) => setAssignTitle(e.target.value)} placeholder="Текст поручения" required />
            <select value={assignAssignee} onChange={(e) => setAssignAssignee(e.target.value)} required>
              <option value="">Исполнитель</option>
              {users.map((u) => (
                <option key={u.id} value={u.username}>{u.username}</option>
              ))}
            </select>
            <input type="date" value={assignDeadline} onChange={(e) => setAssignDeadline(e.target.value)} />
            <button type="submit" className="btn btn-sm btn-primary" disabled={actionLoading}>Создать</button>
          </form>
        </section>

        <section className="detail-card">
          <h2>Версии файлов</h2>
          {doc.versions.length === 0 ? (
            <p className="muted">Нет файлов</p>
          ) : (
            <ul className="versions-list">
              {doc.versions.map((v) => (
                <li key={v.id}>
                  <span className="version-info">
                    v{v.version} — {v.filename} ({formatSize(v.size)})
                  </span>
                  <button
                    type="button"
                    className="btn btn-sm"
                    onClick={() => downloadVersion(doc.id, v.id, v.filename)}
                  >
                    Скачать
                  </button>
                </li>
              ))}
            </ul>
          )}
          <form onSubmit={handleUploadVersion} className="upload-form">
            <input
              type="file"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            />
            <button type="submit" className="btn btn-sm btn-primary" disabled={!uploadFile || actionLoading}>
              {actionLoading ? 'Загрузка…' : 'Добавить версию'}
            </button>
          </form>
        </section>

        <section className="detail-card">
          <h2>Маршрут согласования</h2>
          {sortedSteps.length === 0 ? (
            <p className="muted">Нет шагов</p>
          ) : (
            <>
              <ol className="steps-list">
                {sortedSteps.map((s) => (
                  <li key={s.id} className={s.state}>
                    <span className="step-order">Шаг {s.step_order}</span>
                    <span className="step-approver">
                      {s.delegated_to_username || s.approver_username || `#${s.approver_user_id}`}
                    </span>
                    <span className="step-state">{STEP_STATE_LABELS[s.state] || s.state}</span>
                    {s.deadline && <span className="step-deadline">до {formatDate(s.deadline)}</span>}
                    {s.comment && <span className="step-comment">{s.comment}</span>}
                    {doc.status === 'in_review' && s.state === 'pending' && (
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={() => setDelegateStepId(s.id)}
                      >
                        Делегировать
                      </button>
                    )}
                  </li>
                ))}
              </ol>
              {delegateStepId && (
                <div className="delegate-form">
                  <select value={delegateTo} onChange={(e) => setDelegateTo(e.target.value)}>
                    <option value="">Выберите пользователя</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.username}>{u.username}</option>
                    ))}
                  </select>
                  <button type="button" className="btn btn-sm btn-primary" onClick={handleDelegate} disabled={!delegateTo || actionLoading}>
                    Делегировать
                  </button>
                  <button type="button" className="btn btn-sm" onClick={() => setDelegateStepId(null)}>Отмена</button>
                </div>
              )}
            </>
          )}
        </section>

        <section className="detail-card">
          <h2>ЭЦП (подписи)</h2>
          {(doc.signatures ?? []).length > 0 ? (
            <ul className="signatures-list">
              {doc.signatures.map((s) => (
                <li key={s.id}>
                  <span className="sig-info">
                    {s.cert_subject || `Пользователь #${s.user_id}`} — {formatDate(s.signed_at)}
                  </span>
                  {s.has_detached_signature && (
                    <button
                      type="button"
                      className="btn btn-sm"
                      onClick={() => downloadSignature(doc.id, s.id)}
                    >
                      Скачать .p7s
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">Нет подписей</p>
          )}
          <form onSubmit={handleSign} className="sign-form">
            <div className="form-group">
              <label>Сертификат (CN)</label>
              <input
                value={signCertSubject}
                onChange={(e) => setSignCertSubject(e.target.value)}
                placeholder="ФИО из сертификата"
              />
            </div>
            <div className="form-group">
              <label>Отпечаток сертификата</label>
              <input
                value={signCertThumbprint}
                onChange={(e) => setSignCertThumbprint(e.target.value)}
                placeholder="SHA-1 thumbprint"
              />
            </div>
            <div className="form-group">
              <label>Файл подписи (PKCS#7, необязательно)</label>
              <input
                type="file"
                accept=".p7s,.sig"
                onChange={(e) => setSignatureFile(e.target.files?.[0] || null)}
              />
            </div>
            <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
              {actionLoading ? 'Подписание…' : 'Подписать документ'}
            </button>
          </form>
        </section>

        {doc.status === 'in_review' && (
          <section className="detail-card action-card">
            <h2>Согласование</h2>
            <textarea
              placeholder="Комментарий (необязательно)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
            />
            <div className="action-buttons">
              <button
                type="button"
                className="btn btn-success"
                onClick={handleApprove}
                disabled={actionLoading}
              >
                {actionLoading ? '…' : 'Согласовать'}
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={() => setShowRejectConfirm(true)}
                disabled={actionLoading}
              >
                Отклонить
              </button>
            </div>
            {showRejectConfirm && (
              <div className="confirm-reject">
                <p>Вы уверены, что хотите отклонить документ?</p>
                <button type="button" className="btn btn-danger" onClick={handleReject} disabled={actionLoading}>
                  Да, отклонить
                </button>
                <button type="button" className="btn" onClick={() => setShowRejectConfirm(false)}>
                  Отмена
                </button>
              </div>
            )}
          </section>
        )}

        {showAudit && (
          <section className="detail-card audit-modal">
            <h2>Журнал аудита</h2>
            <ul className="audit-list">
              {auditLog.map((l) => (
                <li key={l.id}>
                  {formatDate(l.created_at)} — {l.actor_username || '?'}: {l.action}
                </li>
              ))}
            </ul>
            <button type="button" className="btn btn-sm" onClick={() => setShowAudit(false)}>Закрыть</button>
          </section>
        )}
      </div>
    </div>
  );
}
