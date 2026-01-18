describe('Chat Flow', () => {
  beforeEach(() => {
    // Use mocks
    cy.mockLogin({
      intercepts: {
        '**/message/history*': {
          statusCode: 200,
          body: [
              {
                sender: 'ai',
                text: 'Olá! Sou seu personal trainer virtual. Como posso ajudar hoje?',
                timestamp: new Date().toISOString()
              }
          ],
          alias: 'chatHistory'
        }
      }
    });

    // Navigate to chat
    cy.get('app-sidebar').contains('Chat').click();
    cy.get('app-chat', { timeout: 10000 }).should('be.visible');
  });

  it('should display the chat interface', () => {
    // Since we mock the trainer profile as 'Atlas', the header should display his name
    cy.contains('h2', 'Atlas').should('exist');
    // And the subtitle
    cy.contains('p', 'Seu Personal Trainer').should('exist');
    
    cy.get('textarea[placeholder*="Digite sua mensagem"]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
  });

  it('should have submit button disabled when message is empty', () => {
    // Clear the textarea field
    cy.get('textarea[name="newMessage"]').clear().should('have.value', '');

    // Button should be disabled - retry logic handles Angular re-renders
    cy.get('button[type="submit"]').should('be.disabled');
  });

  it('should disable textarea while AI is typing', () => {
    // Mock chat response with SSE format
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/event-stream' },
      body: 'data: {"content": "Teste"}\n\ndata: {"content": " de"}\n\ndata: {"content": " resposta"}\n\ndata: [DONE]\n\n',
      delay: 500 // Simulate typing delay
    }).as('chatResponse');

    const userMessage = 'Teste rápido';

    // Send a message
    cy.get('textarea[name="newMessage"]').type(userMessage);
    cy.get('button[type="submit"]').click();

    // While typing, textarea should be disabled
    cy.contains('Digitando').should('be.visible');
    cy.get('textarea[name="newMessage"]').should('be.disabled');
    cy.get('button[type="submit"]').should('be.disabled');

    // Wait for response and check textarea is enabled again
    cy.wait('@chatResponse');
    cy.contains('Digitando', { timeout: 5000 }).should('not.exist');
    cy.get('textarea[name="newMessage"]').should('not.be.disabled');
  });

  it('should send a message and receive a response from the AI', () => {
    // Mock chat response
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: 'Para peito, recomendo supino reto, supino inclinado e crucifixo.',
      delay: 500 
    }).as('chatAI');

    const userMessage = 'Olá, qual o melhor exercício para peito?';

    // Ensure the initial AI message is visible before starting
    cy.get('app-chat').contains('Como posso ajudar hoje?', { timeout: 10000 }).should('be.visible');

    // Send a new message
    cy.get('textarea[placeholder="Digite sua mensagem aqui..."]').type(userMessage);
    cy.get('button[type="submit"]').click();

    // The user's own message should appear
    cy.get('.animate-slide-in-fade').contains(userMessage).should('be.visible');

    // Wait for response
    cy.wait('@chatAI');
    cy.contains('Digitando', { timeout: 5000 }).should('not.exist');

    // Check AI response content
    cy.get('app-chat').contains('recomendo supino reto').should('be.visible');
  });

  it('should reset textarea height after sending a multi-line message', () => {
    // Mock the chat API
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: 'Resposta mock'
    }).as('chatMock');

    const textarea = 'textarea[name="newMessage"]';

    // Get initial height
    cy.get(textarea).then(($el) => {
      const initialHeight = $el[0].offsetHeight;
      
      // Type multi-line message
      cy.get(textarea).type('Linha 1{shift+enter}Linha 2{shift+enter}Linha 3{shift+enter}Linha 4');
      
      // Verify textarea expanded
      cy.get(textarea).should(($expanded) => {
        expect($expanded[0].offsetHeight).to.be.greaterThan(initialHeight);
      });

      // Send message by pressing Enter
      cy.get(textarea).type('{enter}');

      // Verify textarea height reset (with tolerance)
      // Removal of cy.wait(100) - retry mechanism in .should() handles it
      cy.get(textarea).should(($reset) => {
        expect($reset[0].offsetHeight).to.be.lessThan(initialHeight + 20);
      });
    });
  });
});