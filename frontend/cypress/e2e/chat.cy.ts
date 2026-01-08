describe('Chat Flow', () => {
  beforeEach(() => {
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
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

  it('should reset textarea height after sending a multi-line message', () => {
    // Mock the chat API to avoid consuming AI credits
    cy.intercept('POST', '**/chat', {
      statusCode: 200,
      headers: { 'content-type': 'text/event-stream' },
      body: 'data: {"content": "Resposta mock"}\n\ndata: [DONE]\n\n'
    }).as('chatMock');

    const textarea = 'textarea[name="newMessage"]';

    // Get initial height
    cy.get(textarea).then(($el) => {
      const initialHeight = $el[0].offsetHeight;
      
      // Type multi-line message using Shift+Enter for new lines
      cy.get(textarea).type('Linha 1{shift+enter}Linha 2{shift+enter}Linha 3{shift+enter}Linha 4');
      
      // Verify textarea expanded (should be taller than initial)
      cy.get(textarea).should(($expanded) => {
        expect($expanded[0].offsetHeight).to.be.greaterThan(initialHeight);
      });

      // Send message by pressing Enter
      cy.get(textarea).type('{enter}');

      // Wait a bit for the requestAnimationFrame to execute
      cy.wait(100);

      // Verify textarea height reset to initial (or close to it)
      cy.get(textarea).should(($reset) => {
        // Allow some tolerance (within 20px of initial)
        expect($reset[0].offsetHeight).to.be.lessThan(initialHeight + 20);
      });
    });
  });
});