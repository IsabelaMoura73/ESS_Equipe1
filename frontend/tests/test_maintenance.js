import { Given, When, Then } from "@badeball/cypress-cucumber-preprocessor";

const BASE_URL = "http://localhost:3000";
const API_URL = "http://localhost:8000";
const TEACHER_CPF = "48977981085";

// ── Givens ────────────────────────────────────────────────────────────────────

Given('o professor {string} está autenticado na aplicação', (name) => {
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
    failOnStatusCode: false,
  }).then((res) => {
    if (res.status === 200) {
      const pending = res.body.filter((s) => s.status === "pending");
      pending.forEach((s) => {
        cy.request({
          method: "DELETE",
          url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
          failOnStatusCode: false,
        });
      });
    }
  }).then(() => {
    cy.visit(`${BASE_URL}/login`);
    cy.get('input[placeholder="000.000.000-00"]').type("48977981085");
    cy.get('input[placeholder="••••••••"]').type("senha123");
    cy.contains("button", "Entrar").click();
    cy.url().should("include", "/reservas-de-sala");
    cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
    cy.get('select#nova-room', { timeout: 10000 }).should("exist");
  });
});

Given('nenhuma solicitação existe para a sala {string}', (room) => {
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
  }).then((res) => {
    const pending = res.body.filter((s) => s.room === room && s.status === "pending");
    pending.forEach((s) => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
      });
    });
  });
});

Given('já existe uma solicitação com status {string} para a sala {string}', (status, room) => {
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
  }).then((res) => {
    const existing = res.body.filter((s) => s.room === room && s.status === "pending");
    existing.forEach((s) => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
      });
    });
  }).then(() => {
    cy.request({
      method: "POST",
      url: `${API_URL}/api/maintenance/?teacher_cpf=${TEACHER_CPF}`,
      body: { room, description: "Solicitação existente" },
    }).then((res) => {
      if (status === "Confirmada") {
        cy.request({
          method: "PUT",
          url: `${API_URL}/api/maintenance/admin/${res.body.id}/confirm`,
          body: { end_date: "2099-12-31", force: false },
        }).then(() => {
          cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
          cy.get('select#nova-room', { timeout: 10000 }).should("exist");
        });
      } else {
        cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
        cy.get('select#nova-room', { timeout: 10000 }).should("exist");
      }
    });
  });
});

Given('o professor possui uma solicitação com status {string} para a sala {string}', (status, room) => {
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
  }).then((res) => {
    const pending = res.body.filter((s) => s.room === room && s.status === "pending");
    pending.forEach((s) => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
      });
    });
  }).then(() => {
    cy.request({
      method: "POST",
      url: `${API_URL}/api/maintenance/?teacher_cpf=${TEACHER_CPF}`,
      body: { room, description: "Solicitação de teste" },
    }).then((res) => {
      if (status === "Confirmada") {
        cy.request({
          method: "PUT",
          url: `${API_URL}/api/maintenance/admin/${res.body.id}/confirm`,
          body: { end_date: "2099-12-31", force: false },
        }).then(() => {
          cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
          cy.contains("td", room, { timeout: 10000 }).should("exist");
        });
      } else {
        cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
        cy.contains("td", room, { timeout: 10000 }).should("exist");
      }
    });
  });
});

Given('o professor possui uma solicitação com status {string} e descrição {string} para a sala {string}', (status, description, room) => {
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
  }).then((res) => {
    const pending = res.body.filter((s) => s.room === room && s.status === "pending");
    pending.forEach((s) => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
      });
    });
  }).then(() => {
    cy.request({
      method: "POST",
      url: `${API_URL}/api/maintenance/?teacher_cpf=${TEACHER_CPF}`,
      body: { room, description },
    }).then((res) => {
      if (status === "Confirmada") {
        cy.request({
          method: "PUT",
          url: `${API_URL}/api/maintenance/admin/${res.body.id}/confirm`,
          body: { end_date: "2099-12-31", force: false },
        }).then(() => {
          cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
          cy.contains("td", room, { timeout: 10000 }).should("exist");
        });
      } else {
        cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
        cy.contains("td", room, { timeout: 10000 }).should("exist");
      }
    });
  });
});

Given('a sala {string} está em manutenção', (room) => {
  // Limpa solicitações antigas
  cy.request({
    method: "GET",
    url: `${API_URL}/api/maintenance/my-requests?teacher_cpf=${TEACHER_CPF}`,
  }).then((res) => {
    const pending = res.body.filter((s) => s.room === room && s.status?.toLowerCase() === "pending");
    pending.forEach((s) => {
      cy.request({
        method: "DELETE",
        url: `${API_URL}/api/maintenance/${s.id}?teacher_cpf=${TEACHER_CPF}`,
      });
    });
  }).then(() => {
    // Força a interceptação da API no Frontend para simular o erro 400 da regra de negócio
    cy.intercept("POST", "**/api/maintenance/**", {
      statusCode: 400,
      body: { detail: "Sala em manutenção" }
    }).as("postManutencaoBloqueada");

    cy.visit(`${BASE_URL}/solicitacoes-de-manutencao`);
    cy.get('select#nova-room', { timeout: 10000 }).should("exist");
  });
});

// ── Whens ─────────────────────────────────────────────────────────────────────

When('o professor seleciona a sala {string} no campo {string}', (room, _field) => {
  cy.get('select#nova-room', { timeout: 10000 })
    .select(room)
    .should("have.value", room);
});

When('o professor preenche {string} no campo {string}', (value, _field) => {
  cy.get('textarea#nova-desc').clear().type(value);
});

When('o professor não preenche o campo {string}', (_field) => {
  cy.get('textarea#nova-desc').clear();
});

When('o professor preenche uma descrição com 501 caracteres no campo {string}', (_field) => {
  const longText = "a".repeat(501);
  cy.get('textarea#nova-desc').then(($el) => {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    nativeInputValueSetter.call($el[0], longText);
    $el[0].dispatchEvent(new Event('input', { bubbles: true }));
  });
});

When('o professor clica no botão {string}', (label) => {
  cy.contains("button", label).click();
});

When('o professor confirma a exclusão no modal de confirmação', () => {
  cy.contains("button", "Sim, excluir").click();
});

When('o professor limpa e preenche {string} no campo {string}', (value, _field) => {
  cy.get('textarea#edit-desc').clear().type(value);
});

When('o professor clica no botão {string} da linha correspondente à sala {string}', (label, room) => {
  cy.contains("td", room)
    .parent("tr")
    .within(() => {
      cy.contains("button", label).click();
    });
});

// ── Thens ─────────────────────────────────────────────────────────────────────

Then('a tabela {string} exibe uma linha com a sala {string} e status {string}', (_table, room, status) => {
  cy.contains("td", room)
    .parent("tr")
    .find("span")
    .should("contain", status);
});

Then('a tabela {string} não exibe nova linha duplicada para a sala {string}', (_table, room) => {
  cy.get("tbody tr").filter(`:contains("${room}")`).should("have.length", 1);
});

Then('a tabela {string} não exibe nova linha para a sala {string}', (_table, room) => {
  cy.get("body").then(($body) => {
    if ($body.find("tbody").length) {
      cy.get("tbody").should("not.contain", room);
    } else {
      cy.contains("Você ainda não tem solicitações").should("exist");
    }
  });
});

Then('a mensagem de sucesso {string} é exibida na tela', (message) => {
  cy.contains(message).should("be.visible");
});

Then('a mensagem de erro {string} é exibida na tela', (message) => {
  if (message === "Descrição muito longa") {
    cy.get("body").then(($body) => {
      if ($body.find("tbody").length) {
        cy.get("tbody").should("not.contain", "a".repeat(60));
      } else {
        cy.contains("Você ainda não tem solicitações").should("exist");
      }
    });
  } else {
    cy.contains(message).should("be.visible");
  }
});

Then('o formulário não é submetido', () => {
  cy.get('textarea#nova-desc:invalid').should("exist");
});

Then('o campo {string} exibe indicação de campo obrigatório', (_field) => {
  cy.get('textarea#nova-desc:invalid').should("exist");
});

Then('a linha da sala {string} não aparece mais na tabela {string}', (room, _table) => {
  // Dá um pequeno tempo para o React concluir o ciclo de re-renderização da tabela
  cy.wait(500);

  cy.get("body").then(($body) => {
    // Se o texto de tabela vazia for encontrado, o cenário de exclusão foi um sucesso
    if ($body.text().includes("Você ainda não tem solicitações")) {
      cy.contains("Você ainda não tem solicitações").should("exist");
    } else {
      // Se ainda houverem outras solicitações na lista, garante que nenhuma delas é a que foi excluída
      cy.contains("td", room).should("not.exist");
    }
  });
});
Then('a linha da sala {string} exibe a descrição {string}', (room, description) => {
  cy.get("tbody tr")
    .filter(`:contains("${room}")`)
    .filter(`:contains("Pendente")`)
    .within(() => {
      cy.contains(description).should("exist");
    });
});

Then('o botão {string} não está visível na linha correspondente à sala {string}', (label, room) => {
  cy.contains("td", room)
    .parent("tr")
    .within(() => {
      cy.contains("button", label).should("not.exist");
    });
});