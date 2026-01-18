describe('Memories Page', () => {
  beforeEach(() => {
    // 100% Mocked Login
    cy.mockLogin();
  });

  it('should navigate to memories page from sidebar', () => {
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.get('app-memories').should('be.visible');
    cy.contains('h2', 'Minhas Memórias').should('be.visible');
  });

  it('should display subtitle explaining the feature', () => {
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.contains('Estas são as informações que o AI Trainer lembra sobre você').should('be.visible');
  });

  it('should highlight memories menu item when active', () => {
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.get('app-sidebar button').contains('Memórias').parent('button').should('have.class', 'bg-primary');
  });

  it('should show empty state when no memories exist', () => {
    cy.intercept('GET', '**/memory/list*', {
      memories: [], total: 0, page: 1, page_size: 10, total_pages: 0
    }).as('getMemories');
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');
    cy.contains('Nenhuma memória encontrada').should('be.visible');
  });

  it('should display list of memories with dates', () => {
    const mockMemories = {
      memories: [
        { id: 'test-1', memory: 'O usuário prefere treinos pela manhã', created_at: '2026-01-03T08:00:00Z', updated_at: null },
        { id: 'test-2', memory: 'O usuário tem problema no joelho esquerdo', created_at: '2026-01-02T10:30:00Z', updated_at: null }
      ],
      total: 2, page: 1, page_size: 10, total_pages: 1
    };
    cy.intercept('GET', '**/memory/list*', mockMemories).as('getMemories');
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.contains('O usuário prefere treinos pela manhã').should('be.visible');
    cy.contains('O usuário tem problema no joelho esquerdo').should('be.visible');
    cy.get('app-memories button').filter(':contains("Excluir")').should('have.length', 2);
  });

  it('should display pagination controls when multiple pages exist', () => {
    cy.intercept('GET', '**/memory/list*', {
      memories: [{ id: 'test-1', memory: 'Memory 1', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 25, page: 1, page_size: 10, total_pages: 3
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.contains('Página 1 de 3').should('be.visible');
    cy.contains('button', 'Anterior').should('be.visible');
    cy.contains('button', 'Próxima').should('be.visible');
  });

  it('should disable Previous button on first page', () => {
    cy.intercept('GET', '**/memory/list*', {
      memories: [{ id: 'test-1', memory: 'Memory 1', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 25, page: 1, page_size: 10, total_pages: 3
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.contains('button', 'Anterior').should('be.disabled');
    cy.contains('button', 'Próxima').should('not.be.disabled');
  });

  it('should disable Next button on last page', () => {
    cy.intercept('GET', '**/memory/list*', {
      memories: [{ id: 'test-1', memory: 'Memory 1', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 25, page: 3, page_size: 10, total_pages: 3
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.contains('button', 'Anterior').should('not.be.disabled');
    cy.contains('button', 'Próxima').should('be.disabled');
  });

  it('should navigate to next page when clicking Next', () => {
    let callCount = 0;
    cy.intercept('GET', '**/memory/list*', (req) => {
      callCount++;
      if (callCount === 1) {
        req.reply({
          memories: [{ id: 'test-1', memory: 'Page 1 Memory', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
          total: 20, page: 1, page_size: 10, total_pages: 2
        });
      } else {
        req.reply({
          memories: [{ id: 'test-2', memory: 'Page 2 Memory', created_at: '2026-01-02T08:00:00Z', updated_at: null }],
          total: 20, page: 2, page_size: 10, total_pages: 2
        });
      }
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');
    cy.contains('Page 1 Memory').should('be.visible');

    cy.contains('button', 'Próxima').click();
    cy.wait('@getMemories');
    cy.contains('Page 2 Memory').should('be.visible');
    cy.contains('Página 2 de 2').should('be.visible');
  });

  it('should delete memory after confirmation and reload', () => {
    let callCount = 0;
    cy.intercept('GET', '**/memory/list*', (req) => {
      callCount++;
      if (callCount === 1) {
        req.reply({
          memories: [{ id: 'test-1', memory: 'Memory to delete', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
          total: 1, page: 1, page_size: 10, total_pages: 1
        });
      } else {
        req.reply({ memories: [], total: 0, page: 1, page_size: 10, total_pages: 0 });
      }
    }).as('getMemories');
    cy.intercept('DELETE', '**/memory/test-1', { message: 'Memory deleted successfully' }).as('deleteMemory');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.window().then((win) => {
      cy.stub(win, 'confirm').returns(true);
    });

    cy.contains('button', 'Excluir').click();
    cy.wait('@deleteMemory');
    cy.contains('Memória excluída com sucesso').should('be.visible');
  });

  it('should not delete memory when confirmation is cancelled', () => {
    cy.intercept('GET', '**/memory/list*', {
      memories: [{ id: 'test-1', memory: 'Memory to keep', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 1, page: 1, page_size: 10, total_pages: 1
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    cy.window().then((win) => {
      cy.stub(win, 'confirm').returns(false);
    });

    cy.contains('button', 'Excluir').click();
    cy.contains('Memory to keep').should('be.visible');
  });

  it('should navigate back to chat from memories', () => {
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.get('app-memories').should('be.visible');
    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-chat').should('be.visible');
  });
});
