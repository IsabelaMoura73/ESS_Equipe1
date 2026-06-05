import React, { useEffect, useState, useCallback, useRef } from "react";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import Navbar from "../../components/Navbar";

// ── Status ───────────────────────────────────────────────────────────────────

const STATUS = {
  pending:   { label: "Pendente",   bg: "#ffd166", color: "#333" },
  confirmed: { label: "Confirmada", bg: "#06d6a0", color: "#fff" },
  denied:    { label: "Negada",     bg: "#e63946", color: "#fff" },
  completed: { label: "Concluída",  bg: "#4361ee", color: "#fff" },
};

function Badge({ status }) {
  const info = STATUS[status] ?? { label: status, bg: "#ccc", color: "#333" };
  return (
    <span style={{
      display: "inline-block", padding: "2px 10px", borderRadius: "12px",
      fontSize: "0.72rem", fontWeight: "700",
      background: info.bg, color: info.color,
    }}>
      {info.label}
    </span>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return "—";
  const [y, m, d] = dateStr.split("T")[0].split("-");
  return `${d}/${m}/${y}`;
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function Toast({ toast }) {
  if (!toast.text) return null;
  return (
    <div style={{
      ...s.toast,
      background: toast.type === "success" ? "#2dc653" : "#e63946",
      animation: "fadeSlideIn 0.3s ease",
    }}>
      <span style={s.toastIcon}>{toast.type === "success" ? "✓" : "✕"}</span>
      {toast.text}
    </div>
  );
}

// ── Formulário Nova Solicitação ───────────────────────────────────────────────

function NovaSolicitacaoForm({ user, onCreated, onToast }) {
  const [rooms, setRooms] = useState([]);
  const [roomsError, setRoomsError] = useState(false);
  const [roomValue, setRoomValue] = useState("");
  const [descLength, setDescLength] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const descRef = useRef(null);

  useEffect(() => {
    api.get("/api/rooms/?limit=100")
      .then(({ rooms }) => {
        setRooms(rooms);
        if (rooms.length > 0) setRoomValue(rooms[0].name);
      })
      .catch(() => setRoomsError(true));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const description = descRef.current ? descRef.current.value : "";

    if (description.length > 500) {
      setError("Descrição muito longa");
      return;
    }

    setLoading(true);
    try {
      await api.post(
        `/api/maintenance/?teacher_cpf=${encodeURIComponent(user.cpf)}`,
        { room: roomValue, description }
      );
      if (descRef.current) descRef.current.value = "";
      setDescLength(0);
      onCreated();
      onToast("success", "Solicitação criada com sucesso");
    } catch (err) {
      const msgErro = err.response?.data?.detail || err.message || "Erro ao criar solicitação";
      setError(msgErro);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.card}>
      <h2 style={s.cardTitle}>Nova Solicitação de Manutenção</h2>
      <form onSubmit={handleSubmit} style={s.form}>
        <div style={s.field}>
          <label style={s.label} htmlFor="nova-room">Sala</label>
          {roomsError ? (
            <input
              id="nova-room" style={s.input}
              value={roomValue} onChange={(e) => setRoomValue(e.target.value)}
              placeholder="Ex: D005" required
            />
          ) : (
            <select
              id="nova-room" style={s.input}
              value={roomValue} onChange={(e) => setRoomValue(e.target.value)} required
            >
              {rooms.map((r) => (
                <option key={r.name} value={r.name}>{r.name}</option>
              ))}
            </select>
          )}
        </div>

        <div style={s.field}>
          <label style={s.label} htmlFor="nova-desc">
            Descrição <span style={s.required}>*</span>
          </label>
          <textarea
            id="nova-desc" style={s.textarea} rows={4}
            placeholder="Descreva o problema ou motivo da solicitação de manutenção..."
            ref={descRef}
            onInput={(e) => setDescLength(e.target.value.length)}
            onChange={(e) => setDescLength(e.target.value.length)}
            required
          />
          <span style={s.charCount}>{descLength}/500</span>
        </div>

        {error && <p style={s.error}>{error}</p>}

        <div style={{ marginTop: "0.25rem" }}>
          <button type="submit" style={s.btn} disabled={loading}>
            {loading ? "Enviando..." : "Enviar solicitação"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Modal de Edição ───────────────────────────────────────────────────────────

function EditarModal({ solicitacao, user, onSaved, onClose }) {
  const [form, setForm] = useState({ description: solicitacao.description });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.description.trim() === solicitacao.description.trim()) {
      onClose();
      return;
    }
    setLoading(true);
    try {
      await api.put(
        `/api/maintenance/${solicitacao.id}?teacher_cpf=${encodeURIComponent(user.cpf)}`,
        { description: form.description }
      );
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.overlay}>
      <div style={s.modal}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
          <h2 style={s.modalTitle}>Editar Solicitação</h2>
          <button style={s.closeBtn} onClick={onClose} type="button">✕</button>
        </div>

        <div style={{ marginBottom: "1rem" }}>
          <p style={s.metaLabel}>SALA</p>
          <p style={s.metaValue}>{solicitacao.room}</p>
        </div>

        <form onSubmit={handleSubmit} style={s.form}>
          <div style={s.field}>
            <label style={s.label} htmlFor="edit-desc">Descrição</label>
            <textarea
              id="edit-desc" style={s.textarea} rows={4}
              value={form.description}
              onChange={(e) => setForm({ description: e.target.value })}
              maxLength={500} required
            />
            <span style={s.charCount}>{form.description.length}/500</span>
          </div>

          {error && <p style={s.error}>{error}</p>}

          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
            <button type="submit" style={s.btn} disabled={loading}>
              {loading ? "Salvando..." : "Salvar alterações"}
            </button>
            <button type="button" style={s.btnSecondary} onClick={onClose}>
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Modal de Confirmação de Exclusão ──────────────────────────────────────────

function ExcluirModal({ solicitacao, onConfirm, onClose }) {
  return (
    <div style={s.overlay}>
      <div style={{ ...s.modal, maxWidth: "380px", textAlign: "center" }}>
        <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>⚠️</div>
        <h2 style={{ ...s.modalTitle, marginBottom: "0.5rem" }}>Excluir solicitação?</h2>
        <p style={{ color: "#555", fontSize: "0.92rem", marginBottom: "1.5rem" }}>
          Você tem certeza que deseja excluir a solicitação de manutenção da sala{" "}
          <strong>{solicitacao.room}</strong>? Esta ação não pode ser desfeita.
        </p>
        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
          <button style={s.btnDanger} type="button" onClick={onConfirm}>
            Sim, excluir
          </button>
          <button style={s.btnSecondary} type="button" onClick={onClose}>
            Voltar
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Linha da tabela ───────────────────────────────────────────────────────────

function SolicitacaoRow({ solicitacao, onEdit, onDelete }) {
  const isPending = solicitacao.status === "pending";

  return (
    <tr>
      <td style={s.td}>{solicitacao.room}</td>
      <td style={{ ...s.td, maxWidth: "260px" }}>
        <span style={s.descText} title={solicitacao.description}>
          {solicitacao.description.length > 60
            ? solicitacao.description.slice(0, 60) + "…"
            : solicitacao.description}
        </span>
      </td>
      <td style={s.td}><Badge status={solicitacao.status} /></td>
      <td style={s.td}>{formatDate(solicitacao.start_date)}</td>
      <td style={s.td}>{formatDate(solicitacao.end_date)}</td>
      <td style={{ ...s.td, display: "flex", gap: "0.4rem" }}>
        {isPending ? (
          <>
            <button style={s.btnSm} type="button" onClick={() => onEdit(solicitacao)}>
              Editar
            </button>
            <button style={{ ...s.btnSm, ...s.btnSmDanger }} type="button" onClick={() => onDelete(solicitacao)}>
              Excluir
            </button>
          </>
        ) : (
          <span style={{ color: "#888", fontSize: "0.8rem", fontWeight: "500" }}>
            Nenhuma ação necessária
          </span>
        )}
      </td>
    </tr>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

export default function ManutencoesDocente() {
  const { user } = useAuth();
  const [solicitacoes, setSolicitacoes] = useState([]);
  const [loading, setLoading]           = useState(true);
  const [listError, setListError]       = useState("");
  const [filtroStatus, setFiltroStatus] = useState("");
  const [editando, setEditando]         = useState(null);
  const [excluindo, setExcluindo]       = useState(null);
  const [toast, setToast]               = useState({ type: "", text: "" });

  const fetchSolicitacoes = useCallback(async () => {
    setLoading(true);
    setListError("");
    try {
      const qs = filtroStatus
        ? `teacher_cpf=${user.cpf}&status=${filtroStatus}`
        : `teacher_cpf=${user.cpf}`;
      const data = await api.get(`/api/maintenance/my-requests?${qs}`);
      setSolicitacoes(data);
    } catch (err) {
      setListError(err.message);
    } finally {
      setLoading(false);
    }
  }, [user.cpf, filtroStatus]);

  useEffect(() => { fetchSolicitacoes(); }, [fetchSolicitacoes]);

  function showToast(type, text) {
    setToast({ type, text });
    setTimeout(() => setToast({ type: "", text: "" }), 4000);
  }

  function handleEdited() {
    setEditando(null);
    showToast("success", "Solicitação atualizada com sucesso");
    fetchSolicitacoes();
  }

  async function confirmDelete() {
    const sol = excluindo;
    try {
      await api.delete(`/api/maintenance/${sol.id}?teacher_cpf=${encodeURIComponent(user.cpf)}`);
      showToast("success", "Solicitação excluída com sucesso");
      setExcluindo(null);
      fetchSolicitacoes();
    } catch (err) {
      const msgErro = err.response?.data?.detail || err.message;
      showToast("error", msgErro);
      setExcluindo(null);
    }
  }

  return (
    <Navbar>
      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(-16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <Toast toast={toast} />

      {editando && (
        <EditarModal
          solicitacao={editando}
          user={user}
          onSaved={handleEdited}
          onClose={() => setEditando(null)}
        />
      )}

      {excluindo && (
        <ExcluirModal
          solicitacao={excluindo}
          onConfirm={confirmDelete}
          onClose={() => setExcluindo(null)}
        />
      )}

      <h1 style={s.pageTitle}>Solicitações de Manutenção</h1>

      <NovaSolicitacaoForm user={user} onCreated={fetchSolicitacoes} onToast={showToast} />

      <div style={s.card}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1.25rem" }}>
          <h2 style={s.cardTitle}>Minhas Solicitações</h2>
          <select
            style={{ ...s.input, width: "auto", padding: "5px 10px", fontSize: "0.82rem" }}
            value={filtroStatus}
            onChange={(e) => setFiltroStatus(e.target.value)}
          >
            <option value="">Todos os status</option>
            {Object.entries(STATUS).map(([key, { label }]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </div>

        {loading   && <p style={s.muted}>Carregando solicitações...</p>}
        {listError && <p style={s.error}>{listError}</p>}

        {!loading && !listError && (
          solicitacoes.length === 0 ? (
            <p style={s.muted}>
              {filtroStatus
                ? "Nenhuma solicitação com este status."
                : "Você ainda não tem solicitações de manutenção."}
            </p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={s.table}>
                <thead>
                  <tr>
                    {["Sala", "Descrição", "Status", "Início Manut.", "Fim Manut.", "Ações"].map((h) => (
                      <th key={h} style={s.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {solicitacoes.map((sol) => (
                    <SolicitacaoRow
                      key={sol.id}
                      solicitacao={sol}
                      onEdit={setEditando}
                      onDelete={setExcluindo}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </Navbar>
  );
}

// ── Estilos (mesma identidade visual do projeto) ──────────────────────────────

const s = {
  pageTitle:    { fontSize: "1.4rem", fontWeight: "700", color: "#1e3a5f", marginBottom: "1.5rem" },
  card:         { background: "#fff", borderRadius: "10px", padding: "1.5rem", marginBottom: "1.25rem", boxShadow: "0 1px 4px rgba(0,0,0,.07)" },
  cardTitle:    { fontSize: "1rem", fontWeight: "700", color: "#1a1a2e", margin: 0 },
  modalTitle:   { fontSize: "1rem", fontWeight: "700", color: "#1a1a2e", margin: 0 },
  form:         { display: "flex", flexDirection: "column", gap: "0.85rem" },
  field:        { display: "flex", flexDirection: "column", gap: "0.35rem" },
  label:        { fontSize: "0.78rem", fontWeight: "600", color: "#555", textTransform: "uppercase", letterSpacing: "0.04em" },
  required:     { color: "#e63946", fontWeight: "700" },
  input:        { width: "100%", padding: "8px 12px", border: "1px solid #d0d0d0", borderRadius: "6px", fontSize: "0.92rem", boxSizing: "border-box", background: "#fff", color: "#1a1a2e" },
  textarea:     { width: "100%", padding: "8px 12px", border: "1px solid #d0d0d0", borderRadius: "6px", fontSize: "0.92rem", boxSizing: "border-box", background: "#fff", color: "#1a1a2e", resize: "vertical", fontFamily: "inherit" },
  charCount:    { fontSize: "0.72rem", color: "#aaa", textAlign: "right" },
  btn:          { background: "#4361ee", color: "#fff", border: "none", borderRadius: "6px", padding: "9px 18px", fontSize: "0.9rem", fontWeight: "700", cursor: "pointer" },
  btnDanger:    { background: "#e63946", color: "#fff", border: "none", borderRadius: "6px", padding: "9px 18px", fontSize: "0.9rem", fontWeight: "700", cursor: "pointer" },
  btnSecondary: { background: "#f0f0f5", color: "#333", border: "none", borderRadius: "6px", padding: "9px 18px", fontSize: "0.9rem", fontWeight: "600", cursor: "pointer" },
  btnSm:        { background: "#4361ee", color: "#fff", border: "none", borderRadius: "5px", padding: "4px 12px", fontSize: "0.8rem", fontWeight: "600", cursor: "pointer" },
  btnSmDanger:  { background: "#e63946" },
  error:        { color: "#e63946", fontSize: "0.84rem", margin: 0 },
  muted:        { color: "#888", fontSize: "0.88rem" },
  table:        { width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" },
  th:           { textAlign: "left", padding: "8px 10px", background: "#f0f0f5", fontSize: "0.78rem", fontWeight: "700", color: "#444" },
  td:           { padding: "8px 10px", borderBottom: "1px solid #eee", verticalAlign: "middle", color: "#1a1a2e" },
  descText:     { display: "block", color: "#555" },
  metaLabel:    { fontSize: "0.72rem", fontWeight: "700", color: "#888", letterSpacing: "0.05em", marginBottom: "2px" },
  metaValue:    { fontSize: "0.95rem", fontWeight: "600", color: "#1a1a2e" },
  overlay:      { position: "fixed", inset: 0, background: "rgba(0,0,0,.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200 },
  modal:        { background: "#fff", borderRadius: "12px", padding: "1.75rem", width: "100%", maxWidth: "460px", boxShadow: "0 8px 32px rgba(0,0,0,.18)" },
  closeBtn:     { background: "none", border: "none", fontSize: "1rem", cursor: "pointer", color: "#888", padding: "2px 6px", borderRadius: "4px" },
  toast:        { position: "fixed", top: "1.25rem", left: "50%", transform: "translateX(-50%)", zIndex: 300, color: "#fff", padding: "0.75rem 1.5rem", borderRadius: "8px", fontSize: "0.92rem", fontWeight: "600", boxShadow: "0 4px 16px rgba(0,0,0,.18)", display: "flex", alignItems: "center", gap: "0.5rem", whiteSpace: "nowrap" },
  toastIcon:    { fontSize: "1rem", fontWeight: "700" },
};