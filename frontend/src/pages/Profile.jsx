import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function Profile({ user, onUpdate }) {
  const [editing, setEditing] = useState(false);
  const [nome, setNome] = useState(user?.nome || "");
  const [senha, setSenha] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSave(e) {
    e.preventDefault();
    setError("");
    setMsg("");
    setLoading(true);
    try {
      const body = { nome, senha };
      if (novaSenha) body.nova_senha = novaSenha;
      const updated = await api.put("/users/me", body);
      onUpdate(updated);
      setMsg("Dados atualizados com sucesso!");
      setEditing(false);
      setSenha("");
      setNovaSenha("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDeactivate() {
    if (!window.confirm("Tem certeza? Sua conta será desativada e reservas canceladas.")) return;
    try {
      await api.delete("/users/me");
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      navigate("/login");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 500 }}>
      <div className="flex-between">
        <h2>Dados do Usuário</h2>
        {!editing && (
          <button className="btn btn-sm" onClick={() => setEditing(true)}>Editar</button>
        )}
      </div>

      {!editing ? (
        <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <p><strong>Nome:</strong> {user?.nome}</p>
          <p><strong>CPF:</strong> {user?.cpf}</p>
          <p><strong>Tipo:</strong> {user?.tipo}</p>
          {user?.matricula && <p><strong>Matrícula:</strong> {user.matricula}</p>}
          {user?.curso && <p><strong>Curso:</strong> {user.curso}</p>}
          {user?.siape && <p><strong>SIAPE:</strong> {user.siape}</p>}
          {msg && <p className="success mt-1">{msg}</p>}
          <button className="btn btn-danger btn-sm mt-2" onClick={handleDeactivate} style={{ alignSelf: "flex-start" }}>
            Desativar conta
          </button>
        </div>
      ) : (
        <form onSubmit={handleSave} style={{ marginTop: "1rem" }}>
          <label>Nome</label>
          <input value={nome} onChange={(e) => setNome(e.target.value)} required />
          <label>Senha atual (obrigatória para confirmar)</label>
          <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} required />
          <label>Nova senha (opcional)</label>
          <input type="password" value={novaSenha} onChange={(e) => setNovaSenha(e.target.value)} maxLength={128} />
          {error && <p className="error">{error}</p>}
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" disabled={loading}>{loading ? "Salvando..." : "Salvar alterações"}</button>
            <button type="button" className="btn btn-danger" onClick={() => { setEditing(false); setError(""); }}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
