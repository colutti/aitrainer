describe('Chat Flow', () => {
  beforeEach(() => {
    cy.login('admin', '123');
  });

  it('should display the chat interface', () => {
    cy.get('app-chat').should('be.visible');
    cy.contains('h2', 'Chat com seu Personal Trainer').should('be.visible');
    cy.get('textarea[placeholder="Digite sua mensagem aqui..."]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
  });

  it('should have submit button disabled when message is empty', () => {
    // Clear the textarea field
    cy.get('textarea[name="newMessage"]').clear();

    // Button should be disabled
    cy.get('button[type="submit"]').should('be.disabled');
  });

  it('should disable textarea while AI is typing', () => {
    const userMessage = 'Teste rápido';

    // Send a message
    cy.get('textarea[name="newMessage"]').type(userMessage);
    cy.get('button[type="submit"]').click();

    // While typing, textarea should be disabled
    cy.contains('Digitando').should('be.visible');
    cy.get('textarea[name="newMessage"]').should('be.disabled');
    cy.get('button[type="submit"]').should('be.disabled');

    // Wait for response and check textarea is enabled again
    cy.contains('Digitando', { timeout: 120000 }).should('not.exist');
    cy.get('textarea[name="newMessage"]').should('not.be.disabled');
  });

  it('should send a message and receive a response from the AI', () => {
    const userMessage = 'Olá, qual o melhor exercício para peito?';

    // Ensure the initial AI message is visible before starting
    cy.get('div.flex.animate-slide-in-fade.justify-start', { timeout: 10000 }).should('be.visible');

    // Send a new message
    cy.get('textarea[placeholder="Digite sua mensagem aqui..."]').type(userMessage);
    cy.get('button[type="submit"]').click();

    // The user's own message should appear on the screen (newest message is first in DOM due to reverse order)
    cy.get('div.flex.animate-slide-in-fade.justify-end').first().should('contain.text', userMessage);

    // Wait for the "typing" indicator to appear, confirming the request is in flight
    cy.contains('Digitando').should('be.visible');

    // Wait for the "typing" indicator to disappear, confirming the response has been received.
    // Use a very long timeout to account for slow API responses.
    cy.contains('Digitando', { timeout: 120000 }).should('not.exist');

    // The first AI message should now be the new response and should not be empty.
    cy.get('div.flex.animate-slide-in-fade.justify-start')
      .first()
      .find('markdown')
      .should('not.be.empty');
  });
});