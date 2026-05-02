import React, { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Home from "./pages/Home";
import Profile from "./pages/Profile";
import AdminDashboard from "./pages/AdminDashboard";
import Navbar from "./components/Navbar";

function PrivateRoute({ children, user }) {
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });

  function onLogin(userData) {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  }

  function onUpdate(userData) {
    setUser(userData);
    localStorage.setItem("user", JSON.stringify(userData));
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login onLogin={onLogin} />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/home"
          element={
            <PrivateRoute user={user}>
              <Navbar user={user} />
              <main><Home user={user} /></main>
            </PrivateRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <PrivateRoute user={user}>
              <Navbar user={user} />
              <main><Profile user={user} onUpdate={onUpdate} /></main>
            </PrivateRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <PrivateRoute user={user}>
              <Navbar user={user} />
              <main><AdminDashboard /></main>
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to={user ? "/home" : "/login"} replace />} />
      </Routes>
    </BrowserRouter>
  );
}
