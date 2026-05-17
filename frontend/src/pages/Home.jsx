import React, { useEffect, useState } from "react";
import { api } from "../api/client";

function ReserveModal({ room, tipo, onClose, onSaved }) {
  const [form, setForm] = useState({
    horario_inicio: "",
    horario_fim: "",
    qtd_computadores: 1,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const body = {
        sala_id: room.id,
        horario_inicio: new Date(form.horario_inicio).toISOString(),
        horario_fim: new Date(form.horario_fim).toISOString(),
        ...(tipo === "lab" ? { qtd_computadores: Number(form.qtd_computadores) } : {}),
      };
      await api.post(`/reservations/${tipo}`, body);
      onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={overlay}>
      <div className="auth-box" style={{ maxWidth: 480 }}>
        <h2 style={{ marginBottom: "1rem" }}>
          Reservar {tipo === "lab" ? "Computadores em" : "Sala"}: {room.nome}
        </h2>
        <form onSubmit={handleSubmit}>
          <label>Início</label>
          <input
            type="datetime-local"
            value={form.horario_inicio}
            onChange={(e) => setForm((f) => ({ ...f, horario_inicio: e.target.value }))}
            required
          />
          <label>Fim</label>
          <input
            type="datetime-local"
            value={form.horario_fim}
            onChange={(e) => setForm((f) => ({ ...f, horario_fim: e.target.value }))}
            required
          />
          {tipo === "lab" && (
            <>
              <label>Nº de Computadores (máx: {room.qtd_computadores})</label>
              <input
                type="number"
                min={1}
                max={room.qtd_computadores}
                value={form.qtd_computadores}
                onChange={(e) => setForm((f) => ({ ...f, qtd_computadores: e.target.value }))}
                required
              />
            </>
          )}
          {error && <p className="error">{error}</p>}
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button type="submit" disabled={loading}>{loading ? "Enviando..." : "Confirmar"}</button>
            <button type="button" className="btn btn-danger" onClick={onClose}>Cancelar</button>
          </div>
        </form>
      </div>
    </div>
  );
}

const overlay = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,.4)",
  display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
};

export default function Home({ user }) {
  const [rooms, setRooms] = useState([]);
  const [reservasSala, setReservasSala] = useState([]);
  const [reservasLab, setReservasLab] = useState([]);
  const [modal, setModal] = useState(null); // { room, tipo }
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/rooms/").then(setRooms).catch(() => {});
    api.get("/reservations/sala").then(setReservasSala).catch(() => {});
    api.get("/reservations/lab").then(setReservasLab).catch(() => {});
  }, []);

  function reloadReservations() {
    api.get("/reservations/sala").then(setReservasSala);
    api.get("/reservations/lab").then(setReservasLab);
  }

  async function cancelSala(id) {
    try {
      await api.delete(`/reservations/sala/${id}`);
      setMsg("Reserva cancelada.");
      reloadReservations();
    } catch (err) {
      setMsg(err.message);
    }
  }

  async function cancelLab(id) {
    try {
      await api.delete(`/reservations/lab/${id}`);
      setMsg("Reserva cancelada.");
      reloadReservations();
    } catch (err) {
      setMsg(err.message);
    }
  }

  function onSaved() {
    setModal(null);
    setMsg("Reserva enviada! Aguarde confirmação do administrador.");
    reloadReservations();
  }

  const myReservasSala = reservasSala.filter((r) => r.usuario_id === user?.id);
  const myReservasLab = reservasLab.filter((r) => r.usuario_id === user?.id);

  return (
    <>
      {modal && (
        <ReserveModal
          room={modal.room}
          tipo={modal.tipo}
          onClose={() => setModal(null)}
          onSaved={onSaved}
        />
      )}

      {msg && <p className="success" style={{ marginBottom: "1rem" }}>{msg}</p>}

      <div className="card">
        <h2>Salas Disponíveis</h2>
        {rooms.length === 0 && <p className="muted">Nenhuma sala cadastrada.</p>}
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Capacidade</th>
              <th>Computadores</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {rooms.map((r) => (
              <tr key={r.id}>
                <td>{r.nome}</td>
                <td>{r.capacidade}</td>
                <td>{r.qtd_computadores}</td>
                <td>
                  {r.em_manutencao
                    ? <span className="badge badge-negada">Manutenção</span>
                    : <span className="badge badge-confirmada">Disponível</span>}
                </td>
                <td style={{ display: "flex", gap: "0.4rem" }}>
                  <button
                    className="btn btn-sm"
                    disabled={r.em_manutencao}
                    onClick={() => setModal({ room: r, tipo: "sala" })}
                  >
                    Reservar Sala
                  </button>
                  {r.qtd_computadores > 0 && (
                    <button
                      className="btn btn-sm"
                      disabled={r.em_manutencao}
                      onClick={() => setModal({ room: r, tipo: "lab" })}
                    >
                      Reservar Lab
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Minhas Reservas de Sala</h2>
        {myReservasSala.length === 0 && <p className="muted">Nenhuma reserva.</p>}
        <table>
          <thead>
            <tr><th>Sala ID</th><th>Início</th><th>Fim</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {myReservasSala.map((r) => (
              <tr key={r.id}>
                <td>{r.sala_id}</td>
                <td>{new Date(r.horario_inicio).toLocaleString("pt-BR")}</td>
                <td>{new Date(r.horario_fim).toLocaleString("pt-BR")}</td>
                <td><span className={`badge badge-${r.status}`}>{r.status}</span></td>
                <td>
                  {r.status === "pendente" && (
                    <button className="btn btn-sm btn-danger" onClick={() => cancelSala(r.id)}>
                      Cancelar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Minhas Reservas de Lab</h2>
        {myReservasLab.length === 0 && <p className="muted">Nenhuma reserva.</p>}
        <table>
          <thead>
            <tr><th>Sala ID</th><th>Computadores</th><th>Início</th><th>Fim</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {myReservasLab.map((r) => (
              <tr key={r.id}>
                <td>{r.sala_id}</td>
                <td>{r.qtd_computadores}</td>
                <td>{new Date(r.horario_inicio).toLocaleString("pt-BR")}</td>
                <td>{new Date(r.horario_fim).toLocaleString("pt-BR")}</td>
                <td><span className={`badge badge-${r.status}`}>{r.status}</span></td>
                <td>
                  {r.status === "pendente" && (
                    <button className="btn btn-sm btn-danger" onClick={() => cancelLab(r.id)}>
                      Cancelar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
