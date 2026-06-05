const BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers, credencials: "include" });

  if (res.status === 204) return null;

  const body = await res.json().catch(() => ({ detail: "Erro desconhecido" }));
  if (!res.ok) throw new Error(body.detail || "Erro na requisição");
  return body;
}

export const api = {
  get:    (path)                  => request(path),
  post:   (path, body, headers)   => request(path, { method: "POST",   body: JSON.stringify(body),  headers }),
  put:    (path, body, headers)   => request(path, { method: "PUT",    body: JSON.stringify(body),  headers }),
  patch:  (path, body, headers)   => request(path, { method: "PATCH",  body: JSON.stringify(body),  headers }),
  delete: (path, headers)         => request(path, { method: "DELETE", headers }),
};
