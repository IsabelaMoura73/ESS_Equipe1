import React, { useEffect, useState } from "react";
import { api } from "../api/client";

function Section({ title, children }) {
  return (
    <div className="card">
      <h2>{title}</h2>
      {children}
    </div>
  );
}

export default function AdminDashboard() {
  const [rooms, setRooms] = useState([]);
  const [reservasSala, setReservasSala] = useState([]);
  const [reservasLab, setReservasLab] = useState([]);
  const [manutencoes, setManutencoes] = useState([]);
  const [newRoom, setNewRoom] = useState({ nome: "", capacidade: "", descricao: "", qtd_computadores: 0 });
  const [msg, setMsg] = useState("");

  function reload() {
    api.get("/rooms/").then(setRooms).catch(() => {});
    api.get("/reservations/sala").then(setReservasSala).catch(() => {});
    api.get("/reservations/lab").then(setReservasLab).catch(() => {});
    api.get("/maintenance/").then(setManutencoes).catch(() => {});
  }

  useEffect(() => { reload(); }, []);

  async function addRoom(e) {
    e.preventDefault();
    try {
      await api.post("/rooms/", {
        ...newRoom,
        capacidade: Number(newRoom.capacidade),
        qtd_computadores: Number(newRoom.qtd_computadores),
      });
      setNewRoom({ nome: "", capacidade: "", descricao: "", qtd_computadores: 0 });
      setMsg("Sala cadastrada!");
      reload();
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function deleteRoom(id) {
    if (!window.confirm("Remover sala?")) return;
    try { await api.delete(`/rooms/${id}`); reload(); } catch (err) { setMsg(err.message); }
  }

  async function toggleMaintenance(room) {
    try {
      await api.put(`/rooms/${room.id}`, { em_manutencao: !room.em_manutencao });
      reload();
    } catch (err) { setMsg(err.message); }
  }

  async function setResSalaStatus(id, status) {
    try {
      await api.patch(`/reservations/sala/${id}/status?status=${status}`);
      reload();
    } catch (err) { setMsg(err.message); }
  }

  async function setResLabStatus(id, status) {
    try {
      await api.patch(`/reservations/lab/${id}/status?status=${status}`);
      reload();
    } catch (err) { setMsg(err.message); }
  }

  async function setManutStatus(id, status) {
    try {
      await api.patch(`/maintenance/${id}/status?status=${status}`);
      reload();
    } catch (err) { setMsg(err.message); }
  }

  const pendingSala = reservasSala.filter((r) => r.status === "pendente");
  const pendingLab = reservasLab.filter((r) => r.status === "pendente");
  const pendingManut = manutencoes.filter((r) => r.status === "pendente");

  return (
    <>
      {msg && <p className="success" style={{ marginBottom: "1rem" }}>{msg}</p>}

      <Section title="Cadastrar Nova Sala">
        <form onSubmit={addRoom} style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
          <div>
            <label>Nome</label>
            <input value={newRoom.nome} onChange={(e) => setNewRoom((f) => ({ ...f, nome: e.target.value }))} required />
          </div>
          <div>
            <label>Capacidade</label>
            <input type="number" value={newRoom.capacidade} onChange={(e) => setNewRoom((f) => ({ ...f, capacidade: e.target.value }))} required />
          </div>
          <div>
            <label>Descrição</label>
            <input value={newRoom.descricao} onChange={(e) => setNewRoom((f) => ({ ...f, descricao: e.target.value }))} />
          </div>
          <div>
            <label>Nº Computadores</label>
            <input type="number" min={0} value={newRoom.qtd_computadores} onChange={(e) => setNewRoom((f) => ({ ...f, qtd_computadores: e.target.value }))} />
          </div>
          <button type="submit" className="btn" style={{ gridColumn: "span 2" }}>Cadastrar</button>
        </form>
      </Section>

      <Section title="Gerenciar Salas">
        <table>
          <thead>
            <tr><th>Nome</th><th>Cap.</th><th>PCs</th><th>Manutenção</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {rooms.map((r) => (
              <tr key={r.id}>
                <td>{r.nome}</td>
                <td>{r.capacidade}</td>
                <td>{r.qtd_computadores}</td>
                <td>
                  <span className={`badge badge-${r.em_manutencao ? "negada" : "confirmada"}`}>
                    {r.em_manutencao ? "Sim" : "Não"}
                  </span>
                </td>
                <td style={{ display: "flex", gap: "0.4rem" }}>
                  <button className="btn btn-sm" onClick={() => toggleMaintenance(r)}>
                    {r.em_manutencao ? "Liberar" : "Manutenção"}
                  </button>
                  <button className="btn btn-sm btn-danger" onClick={() => deleteRoom(r.id)}>Remover</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title={`Reservas de Sala Pendentes (${pendingSala.length})`}>
        {pendingSala.length === 0 && <p className="muted">Nenhuma pendente.</p>}
        <table>
          <thead><tr><th>ID</th><th>Usuário</th><th>Sala</th><th>Início</th><th>Fim</th><th>Ações</th></tr></thead>
          <tbody>
            {pendingSala.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.usuario_id}</td>
                <td>{r.sala_id}</td>
                <td>{new Date(r.horario_inicio).toLocaleString("pt-BR")}</td>
                <td>{new Date(r.horario_fim).toLocaleString("pt-BR")}</td>
                <td style={{ display: "flex", gap: "0.4rem" }}>
                  <button className="btn btn-sm" onClick={() => setResSalaStatus(r.id, "confirmada")}>Confirmar</button>
                  <button className="btn btn-sm btn-danger" onClick={() => setResSalaStatus(r.id, "negada")}>Negar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title={`Reservas de Lab Pendentes (${pendingLab.length})`}>
        {pendingLab.length === 0 && <p className="muted">Nenhuma pendente.</p>}
        <table>
          <thead><tr><th>ID</th><th>Usuário</th><th>Sala</th><th>PCs</th><th>Início</th><th>Fim</th><th>Ações</th></tr></thead>
          <tbody>
            {pendingLab.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.usuario_id}</td>
                <td>{r.sala_id}</td>
                <td>{r.qtd_computadores}</td>
                <td>{new Date(r.horario_inicio).toLocaleString("pt-BR")}</td>
                <td>{new Date(r.horario_fim).toLocaleString("pt-BR")}</td>
                <td style={{ display: "flex", gap: "0.4rem" }}>
                  <button className="btn btn-sm" onClick={() => setResLabStatus(r.id, "confirmada")}>Confirmar</button>
                  <button className="btn btn-sm btn-danger" onClick={() => setResLabStatus(r.id, "negada")}>Negar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title={`Solicitações de Manutenção Pendentes (${pendingManut.length})`}>
        {pendingManut.length === 0 && <p className="muted">Nenhuma pendente.</p>}
        <table>
          <thead><tr><th>ID</th><th>Usuário</th><th>Sala</th><th>Descrição</th><th>Ações</th></tr></thead>
          <tbody>
            {pendingManut.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.usuario_id}</td>
                <td>{r.sala_id}</td>
                <td>{r.descricao}</td>
                <td style={{ display: "flex", gap: "0.4rem" }}>
                  <button className="btn btn-sm" onClick={() => setManutStatus(r.id, "aprovada")}>Aprovar</button>
                  <button className="btn btn-sm btn-danger" onClick={() => setManutStatus(r.id, "negada")}>Negar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </>
  );
}
