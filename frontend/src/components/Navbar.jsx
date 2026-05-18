import React from "react";
import { Link, useNavigate } from "react-router-dom";

export default function Navbar({ user }) {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  }

  return (
    <nav>
      <Link to="/home" className="brand">Salla</Link>
      <div>
        {user?.tipo === "admin" && <Link to="/admin">Admin</Link>}
        <Link to="/home">Salas</Link>
        <Link to="/profile">Meu Perfil</Link>
        <button className="logout" onClick={logout}>Sair</button>
      </div>
    </nav>
  );
}
