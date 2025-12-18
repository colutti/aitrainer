describe('Chat Flow', () => {
  beforeEach(() => {
    cy.login('admin', '123');
  });

  it('should display the chat interface', () => {
    cy.get('app-chat').should('be.visible');
    cy.contains('h2', 'Chat com seu Personal Trainer').should('be.visible');
    cy.get('input[placeholder="Digite sua mensagem aqui..."]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
  });

  it('should send a message and receive a response from the AI', () => {
    const userMessage = 'Olá, qual o melhor exercício para peito?';

    // Ensure the initial AI message is visible before starting
    cy.get('div.flex.animate-slide-in-fade.justify-start', { timeout: 10000 }).should('be.visible');

    // Send a new message
    cy.get('input[placeholder="Digite sua mensagem aqui..."]').type(userMessage);
    cy.get('button[type="submit"]').click();

    // The user's own message should appear on the screen
    cy.get('div.flex.animate-slide-in-fade.justify-end').last().should('contain', userMessage);

    // Wait for the "typing" indicator to appear, confirming the request is in flight
    cy.contains('Digitando').should('be.visible');

    // Wait for the "typing" indicator to disappear, confirming the response has been received.
    // Use a very long timeout to account for slow API responses.
    cy.contains('Digitando', { timeout: 120000 }).should('not.exist');

    // The last AI message should now be the new response and should not be empty.
    cy.get('div.flex.animate-slide-in-fade.justify-start')
      .last()
      .find('p.text-sm')
      .invoke('text')
      .should('not.be.empty');
  });
});