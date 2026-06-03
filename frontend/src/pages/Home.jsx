import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const REDIRECT = {
  discente: "/reservas-de-sala",
  docente:  "/reservas-de-sala",
  admin:    "/salas",
};

export default function Home() {
  const { user } = useAuth();

  return (
    <div style={styles.wrapper}>
      <div style={styles.bg} aria-hidden="true">
        {[...Array(6)].map((_, i) => (
          <div key={i} style={{ ...styles.circle, ...circlePos[i] }} />
        ))}
      </div>

      <nav style={styles.nav}>
        <span style={styles.brand}>Salla</span>
        <div style={styles.navLinks}>
          {user ? (
            <Link to={REDIRECT[user.tipo] || "/perfil"} style={styles.navBtn}>Meu painel →</Link>
          ) : (
            <>
              <Link to="/login" style={styles.navLink}>Entrar</Link>
              <Link to="/cadastro" style={styles.navBtn}>Cadastrar-se</Link>
            </>
          )}
        </div>
      </nav>

      <main style={styles.main}>
        <div style={styles.badge}>ESS 2026.1 - Equipe 1</div>
        <h1 style={styles.title}>
          Reserve salas e<br />
          <span style={styles.highlight}>laboratórios</span><br />
          com facilidade.
        </h1>
        <p style={styles.subtitle}>
          Salla é o sistema de reserva de espaços da universidade. Docentes e
          discentes podem solicitar salas e laboratórios de forma rápida, com
          aprovação centralizada pela administração.
        </p>

        <div style={styles.actions}>
          {user ? (
            <Link to={REDIRECT[user.tipo] || "/perfil"} style={styles.ctaPrimary}>Acessar meu painel</Link>
          ) : (
            <>
              <Link to="/cadastro" style={styles.ctaPrimary}>Começar agora</Link>
              <Link to="/login" style={styles.ctaSecondary}>Já tenho conta</Link>
            </>
          )}
        </div>

        <div style={styles.features}>
          {featureList.map((f) => (
            <div key={f.title} style={styles.featureCard}>
              <span style={styles.featureIcon}>{f.icon}</span>
              <strong style={styles.featureTitle}>{f.title}</strong>
              <p style={styles.featureText}>{f.desc}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

const featureList = [
  {
    icon: "🏛️",
    title: "Salas e Laboratórios",
    desc: "Consulte a disponibilidade e reserve o espaço certo para sua aula ou estudo.",
  },
  {
    icon: "✅",
    title: "Aprovação centralizada",
    desc: "Solicitações passam pela administração, garantindo organização e transparência.",
  },
  {
    icon: "👤",
    title: "Perfis por vínculo",
    desc: "Acesso diferenciado para discentes, docentes e administradores.",
  },
];

const circlePos = [
  { top: "-80px", right: "-80px", width: "320px", height: "320px", opacity: 0.07 },
  { top: "30%", left: "-120px", width: "250px", height: "250px", opacity: 0.05 },
  { bottom: "-60px", right: "20%", width: "200px", height: "200px", opacity: 0.06 },
  { top: "10%", right: "25%", width: "80px", height: "80px", opacity: 0.1 },
  { bottom: "20%", left: "10%", width: "120px", height: "120px", opacity: 0.07 },
  { top: "60%", right: "5%", width: "60px", height: "60px", opacity: 0.12 },
];

const styles = {
  wrapper: {
    minHeight: "100vh",
    background: "#0f1117",
    color: "#f0f0f0",
    position: "relative",
    overflow: "hidden",
    fontFamily: "'Georgia', serif",
  },
  bg: {
    position: "absolute",
    inset: 0,
    pointerEvents: "none",
  },
  circle: {
    position: "absolute",
    borderRadius: "50%",
    background: "#4361ee",
  },
  nav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "1.5rem 2.5rem",
    position: "relative",
    zIndex: 10,
    borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  brand: {
    fontSize: "1.5rem",
    fontWeight: "700",
    letterSpacing: "-0.03em",
    color: "#fff",
  },
  navLinks: {
    display: "flex",
    alignItems: "center",
    gap: "1.5rem",
  },
  navLink: {
    color: "#aaa",
    textDecoration: "none",
    fontSize: "0.9rem",
  },
  navBtn: {
    background: "#4361ee",
    color: "#fff",
    textDecoration: "none",
    padding: "7px 18px",
    borderRadius: "6px",
    fontSize: "0.9rem",
    fontWeight: "600",
  },
  main: {
    maxWidth: "780px",
    margin: "0 auto",
    padding: "5rem 2rem 4rem",
    position: "relative",
    zIndex: 10,
  },
  badge: {
    display: "inline-block",
    background: "rgba(67,97,238,0.15)",
    border: "1px solid rgba(67,97,238,0.3)",
    color: "#7b96ff",
    padding: "4px 14px",
    borderRadius: "20px",
    fontSize: "0.78rem",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    marginBottom: "2rem",
  },
  title: {
    fontSize: "clamp(2.4rem, 6vw, 4rem)",
    lineHeight: 1.1,
    fontWeight: "700",
    letterSpacing: "-0.03em",
    marginBottom: "1.5rem",
    color: "#fff",
  },
  highlight: {
    color: "#4361ee",
  },
  subtitle: {
    fontSize: "1.05rem",
    lineHeight: 1.7,
    color: "#888",
    maxWidth: "520px",
    marginBottom: "2.5rem",
    fontFamily: "system-ui, sans-serif",
  },
  actions: {
    display: "flex",
    gap: "1rem",
    flexWrap: "wrap",
    marginBottom: "4rem",
  },
  ctaPrimary: {
    background: "#4361ee",
    color: "#fff",
    textDecoration: "none",
    padding: "12px 28px",
    borderRadius: "8px",
    fontWeight: "700",
    fontSize: "0.95rem",
    fontFamily: "system-ui, sans-serif",
  },
  ctaSecondary: {
    background: "transparent",
    color: "#aaa",
    textDecoration: "none",
    padding: "12px 28px",
    borderRadius: "8px",
    fontWeight: "600",
    fontSize: "0.95rem",
    border: "1px solid rgba(255,255,255,0.12)",
    fontFamily: "system-ui, sans-serif",
  },
  features: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "1rem",
  },
  featureCard: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: "10px",
    padding: "1.25rem",
    display: "flex",
    flexDirection: "column",
    gap: "0.4rem",
  },
  featureIcon: {
    fontSize: "1.4rem",
  },
  featureTitle: {
    fontSize: "0.9rem",
    color: "#eee",
    fontFamily: "system-ui, sans-serif",
  },
  featureText: {
    fontSize: "0.82rem",
    color: "#666",
    lineHeight: 1.5,
    fontFamily: "system-ui, sans-serif",
  },
};
