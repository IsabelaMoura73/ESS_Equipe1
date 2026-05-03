# Como Executar o Projeto

Este guia explica como subir o frontend e o backend localmente com apenas 3 comandos.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Download |
|:-----------|:-------------|:---------|
| Node.js    | 18+          | https://nodejs.org |
| Python     | 3.10+        | https://python.org |
| pip        | (vem com Python) | — |

---

## 1. Instalar dependências do Frontend

Execute dentro da pasta `frontend/`:

```bash
npm install
```

Este comando instala o React, React Router e o Parcel (bundler).

---

## 2. Instalar dependências do Backend

Execute dentro da pasta `backend/`:

```bash
pip install -r requirements.txt
```

Isso instala FastAPI, Uvicorn, SQLAlchemy, python-jose (JWT), passlib (bcrypt) e Pydantic.

> O banco de dados SQLite (`salla.db`) é criado automaticamente na primeira execução — nenhuma configuração necessária.

---

## 3. Rodar o Frontend

Execute dentro da pasta `frontend/`:

```bash
npm run dev
```

O servidor de desenvolvimento inicia em: **http://localhost:3000**

---

## 4. Rodar o Backend

Execute dentro da pasta `backend/`:

```bash
python -m uvicorn main:app --reload
```

A API inicia em: **http://localhost:8000**

Documentação interativa (Swagger): **http://localhost:8000/docs**

---

## Resumo — 3 comandos para rodar tudo

```bash
# Terminal 1 — Frontend
cd frontend
npm install
npm run dev

# Terminal 2 — Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

---

## Portas utilizadas

| Serviço  | Porta |
|:---------|:------|
| Frontend | 3000  |
| Backend  | 8000  |

---

**Equipe 1 — ESS 2026.1 — CIn UFPE**
