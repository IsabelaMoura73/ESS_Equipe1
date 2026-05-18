# Sistema de Reserva de Salas e Equipamentos - Equipe 1

Este repositório contém o monorepo do projeto desenvolvido para a disciplina de **Engenharia de Software e Sistemas (ESS)**, lecionada pelo professor **Breno Miranda** no período **2026.1** no **CIn - UFPE**.

## 📌 O Projeto
A aplicação tem como objetivo principal gerenciar a reserva de salas e computadores de laboratório, além de permitir solicitações de manutenção. O sistema atende a diferentes perfis de usuários (Discentes, Docentes e Administradores) com fluxos de aprovação integrados.

---

## 📅 Cronograma (Equipe 1)

| Data | Horário | Marco do Projeto |
| :--- | :--- | :--- |
| **28/Abr (Terça)** | **15:00** | **Primeira Entrega**: Apresentação dos Cenários. |
| **19/Mai (Terça)** | **15:00** | **Segunda Entrega**: Backend + Testes. |
| **11/Jun (Quinta)** | **13:00** | **Apresentação Final**: Sistema em funcionamento e execução dos testes. |

---

## 🛠 Stack Tecnológica

O projeto foi construído utilizando tecnologias modernas para garantir escalabilidade e simplicidade:

* **Frontend:** React, JavaScript e CSS puro.
* **Backend:** FastAPI (Python).
* **Banco de Dados:** PostgreSQL via Supabase.

---

## 👥 Perfis de Usuário e Funcionalidades

### 🎓 Usuários (Discentes e Docentes)
* **Cadastro e Perfil:** Registro obrigatório com CPF, nome, senha e vínculo.
    * **Discentes:** Devem informar Curso e Matrícula.
    * **Docentes:** Devem informar o SIAPE.
* **Reservas:** Efetuar, editar, cancelar e visualizar o histórico de reservas de salas ou computadores.
* **Solicitações (Docentes):** Criar solicitações de manutenção para salas específicas.
* **Avaliações:** Realizar reviews de salas e equipamentos.

### 🔑 Administradores
* **Gestão de Salas:** Cadastro (Nome, Capacidade, Descrição e total de Computadores), edição e remoção de salas.
* **Moderação:** Confirmar ou negar reservas e solicitações de manutenção.
* **Controle de Manutenção:** Definir períodos de manutenção, o que bloqueia automaticamente novas reservas e nega pendências existentes.

---

## 📋 Regras de Negócio Importantes

* **Prioridade:** Reservas feitas por professores têm prioridade visual na fila de aprovação do administrador.
* **Restrição de Horário:** Um usuário só pode possuir **uma única reserva** por data/horário].
* **Edição/Cancelamento:** Só é permitido editar ou cancelar reservas e solicitações que ainda estejam com o status **Pendente**.
* **Estados da Reserva:**
    1.  **Pendente:** Aguardando admin.
    2.  **Confirmada:** Aprovada pelo admin.
    3.  **Negada:** Rejeitada pelo admin.
    4.  **Concluída:** Quando o horário da reserva confirmada já passou.
* **Segurança:** O login é realizado via CPF e Senha (máximo 128 caracteres). Não há recuperação de senha ou foto de perfil.

---

## 🗂️ Estrutura de Dados (Principais Objetos)

| Objeto | Atributos Principais |
| :--- | :--- |
| **Sala** | Nome, Capacidade, Descrição, Qtd Computadores, Status Manutenção |
| **Usuário** | Nome, CPF, Senha, Tipo (Docente/Discente), SIAPE/Matrícula, Curso |
| **Reserva de Sala** | Usuário, Sala, Horário Início, Horário Fim, Status |
| **Reserva de Computador** | Usuário, Sala, Qtd Computadores, Horário Início/Fim, Status |
| **Solicitação Manutenção**| Usuário, Sala, Descrição, Data Início/Fim |

---

## 🚀 Como Executar o Backend

1. Crie o ambiente virtual e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
```

2. Preencha o arquivo `.env` com as chaves do Supabase. A `DATABASE_URL` precisa ser a URL completa de conexão do PostgreSQL/pooler, incluindo usuário e senha.

3. No SQL Editor do Supabase, execute apenas o complemento da feature de equipamentos, caso essas tabelas ainda nao existam:

```bash
sql/schema.sql
```

Esse SQL nao substitui o schema principal do grupo. Ele usa a tabela `public.users` ja existente e adiciona somente `equipment` e `equipment_reservations`.

4. Suba a API:

```bash
cd backend
uvicorn main:app --reload
```

5. Acesse a documentação interativa:

```text
http://127.0.0.1:8000/docs
```

## ✅ Testes

Os testes cobrem os cenários da feature de reserva de equipamentos usando banco em memória:

```bash
cd backend
pytest
```

---
**Equipe 1 - ESS 2026.1**
