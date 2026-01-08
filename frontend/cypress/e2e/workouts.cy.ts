
describe('Workouts Page', () => {
  beforeEach(() => {
    // Login antes de cada teste
    cy.visit('/login');
    // Esperar inputs estarem prontos
    cy.get('input[type="email"]').should('be.visible').clear().type('cypress_user@test.com', { delay: 100 });
    cy.get('input[type="password"]').type('Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    
    // Verificar botão habilitado antes de clicar
    cy.get('button').contains('Entrar').should('not.be.disabled').click();
    
    // Esperar redirecionamento para o chat (página inicial)
    cy.url({ timeout: 15000 }).should('include', '/chat');
    // Esperar um pouco para garantir que o sidebar carregou
    cy.get('nav').should('be.visible');
  });

  it('should navigate to Workouts page via sidebar', () => {
    // Verificar se o link está no sidebar (assumindo que o texto é "Meus Treinos")
    cy.get('nav').contains('Meus Treinos').should('be.visible').click();

    // Validar URL
    cy.url().should('include', '/workouts');

    // Validar Título/Header
    cy.get('h2').contains('Meus Treinos').should('be.visible');
  });

  it('should display workout list or empty state', () => {
    cy.visit('/workouts');

    // Verifica se carrega a lista OU o estado vazio
    cy.get('app-workouts').should('exist');
    
    // Como criamos um treino no teste manual, deve aparecer "Supino Reto"
    // Mas para ser robusto, verificamos container de cards ou mensagem de vazio
    cy.get('body').then(($body) => {
        if ($body.find('app-workout-card').length > 0) {
            cy.log('Workouts found');
            cy.get('app-workout-card').should('have.length.gt', 0);
            cy.contains('Supino Reto').should('exist');
        } else {
            cy.log('No workouts found (Empty State)');
            cy.contains('Nenhum treino registrado').should('be.visible');
        }
    });
  });
});
