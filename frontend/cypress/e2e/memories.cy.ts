describe('Memories Page', () => {
  beforeEach(() => {
    cy.login('admin', '123');
    cy.get('app-sidebar').should('be.visible');
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
    // Intercept API to return empty list
    cy.intercept('GET', '**/memory/list', { memories: [], total: 0 }).as('getMemories');
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');
    cy.contains('Nenhuma memória encontrada').should('be.visible');
    cy.contains('Suas memórias serão criadas conforme você conversa').should('be.visible');
  });

  it('should display list of memories with dates', () => {
    const mockMemories = {
      memories: [
        {
          id: 'test-1',
          memory: 'O usuário prefere treinos pela manhã',
          created_at: '2026-01-03T08:00:00Z',
          updated_at: null
        },
        {
          id: 'test-2',
          memory: 'O usuário tem problema no joelho esquerdo',
          created_at: '2026-01-02T10:30:00Z',
          updated_at: null
        }
      ],
      total: 2
    };
    cy.intercept('GET', '**/memory/list', mockMemories).as('getMemories');
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    // Verify memories are displayed
    cy.contains('O usuário prefere treinos pela manhã').should('be.visible');
    cy.contains('O usuário tem problema no joelho esquerdo').should('be.visible');

    // Verify delete buttons are present (one for each memory)
    cy.get('app-memories button').filter(':contains("Excluir")').should('have.length', 2);
  });

  it('should show delete button for each memory', () => {
    cy.intercept('GET', '**/memory/list', {
      memories: [{ id: 'test-1', memory: 'Test memory', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 1
    }).as('getMemories');
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');
    cy.contains('button', 'Excluir').should('be.visible');
  });

  it('should delete memory after confirmation and reload the list', () => {
    // Setup intercepts for both initial load and reload
    let callCount = 0;
    cy.intercept('GET', '**/memory/list', (req) => {
      callCount++;
      if (callCount === 1) {
        req.reply({
          memories: [{ id: 'test-1', memory: 'Memory to delete', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
          total: 1
        });
      } else {
        req.reply({ memories: [], total: 0 });
      }
    }).as('getMemories');
    cy.intercept('DELETE', '**/memory/test-1', { message: 'Memory deleted successfully' }).as('deleteMemory');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    // Stub confirm to return true, then click delete
    cy.window().then((win) => {
      cy.stub(win, 'confirm').returns(true);
    });

    cy.contains('button', 'Excluir').click();
    cy.wait('@deleteMemory');

    // Verify success message appears
    cy.contains('Memória excluída com sucesso').should('be.visible');
  });


  it('should not delete memory when confirmation is cancelled', () => {
    cy.intercept('GET', '**/memory/list', {
      memories: [{ id: 'test-1', memory: 'Memory to keep', created_at: '2026-01-03T08:00:00Z', updated_at: null }],
      total: 1
    }).as('getMemories');

    cy.get('app-sidebar button').contains('Memórias').click();
    cy.wait('@getMemories');

    // Stub confirm to return false (cancel)
    cy.window().then((win) => {
      cy.stub(win, 'confirm').returns(false);
    });

    cy.contains('button', 'Excluir').click();

    // Verify memory is still there
    cy.contains('Memory to keep').should('be.visible');
  });

  it('should navigate back to chat from memories', () => {
    cy.get('app-sidebar button').contains('Memórias').click();
    cy.get('app-memories').should('be.visible');

    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-chat').should('be.visible');
  });
});

