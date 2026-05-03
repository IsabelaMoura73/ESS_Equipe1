import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";

export default function Register() {
  const [form, setForm] = useState({
    nome: "", cpf: "", senha: "", tipo: "discente",
    matricula: "", curso: "", siape: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  function set(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/users/register", form);
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-box">
        <h1>Cadastro de Usuário</h1>
        <form onSubmit={handleSubmit}>
          <label>Nome</label>
          <input value={form.nome} onChange={set("nome")} required />

          <label>CPF</label>
          <input placeholder="000.000.000-00" value={form.cpf} onChange={set("cpf")} required />

          <label>Tipo de Vínculo</label>
          <select value={form.tipo} onChange={set("tipo")}>
            <option value="discente">Discente</option>
            <option value="docente">Docente</option>
          </select>

          {form.tipo === "discente" && (
            <>
              <label>Matrícula</label>
              <input value={form.matricula} onChange={set("matricula")} required />
              <label>Curso</label>
              <input value={form.curso} onChange={set("curso")} required />
            </>
          )}

          {form.tipo === "docente" && (
            <>
              <label>SIAPE</label>
              <input value={form.siape} onChange={set("siape")} required />
            </>
          )}

          <label>Senha</label>
          <input type="password" value={form.senha} onChange={set("senha")} maxLength={128} required />

          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Cadastrando..." : "Confirmar"}
          </button>
        </form>
        <p className="muted mt-2">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
