describe('Chat Flow', () => {
  beforeEach(() => {
    // Intercept Login
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');

    // Intercept chat history (initial load)
    cy.intercept('GET', '**/message/history*', {
      statusCode: 200,
      body: {
        messages: [
          {
            sender: 'ai',
            content: 'Olá! Sou seu personal trainer virtual. Como posso ajudar hoje?',
            timestamp: new Date().toISOString()
          }
        ]
      }
    }).as('chatHistory');

    // Intercept stats (dashboard loads on login)
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    
    // Intercept Trainer Profile (new req in Chat)
    cy.intercept('GET', '**/trainer/trainer_profile', {
        statusCode: 200,
        body: { trainer_type: 'atlas' }
    }).as('trainerProfile');

    // Intercept Available Trainers (new req in Chat)
    cy.intercept('GET', '**/trainer/available_trainers', {
        statusCode: 200,
        body: [{ 
            trainer_id: 'atlas', 
            name: 'Atlas', 
            avatar_url: '/assets/atlas.png' 
        }]
    }).as('availableTrainers');

    cy.login('cypress_user@test.com', 'password123');
    
    // Navigate to chat
    cy.get('button').contains('Chat').click();
    cy.wait(['@chatHistory', '@trainerProfile', '@availableTrainers']);
  });

  it('should display the chat interface', () => {
    cy.get('app-chat').should('be.visible');
    // Since we mock the trainer profile as 'Atlas', the header should display his name
    cy.contains('h2', 'Atlas').should('be.visible');
    // And the subtitle
    cy.contains('p', 'Seu Personal Trainer').should('be.visible');
    
    cy.get('textarea[placeholder*="Digite sua mensagem"]').should('be.visible');
    cy.get('button[type="submit"]').should('be.visible');
  });

  it('should have submit button disabled when message is empty', () => {
    // Clear the textarea field
    cy.get('textarea[name="newMessage"]').clear();

    // Button should be disabled
    cy.get('button[type="submit"]').should('be.disabled');
  });

  it('should disable textarea while AI is typing', () => {
    // Mock chat response with SSE format
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/event-stream' },
      body: 'data: {"content": "Teste"}\n\ndata: {"content": " de"}\n\ndata: {"content": " resposta"}\n\ndata: [DONE]\n\n',
      delay: 1000 // Simulate typing delay
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
    // Mock chat response with delay to allow "Digitando" to appear
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: 'Para peito, recomendo supino reto, supino inclinado e crucifixo.',
      delay: 500 // Allow typing indicator to show
    }).as('chatAI');

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

    // Wait for response
    cy.wait('@chatAI');
    cy.contains('Digitando', { timeout: 5000 }).should('not.exist');

    // The first AI message should now be the new response and should not be empty.
    cy.get('div.flex.animate-slide-in-fade.justify-start')
      .first()
      .find('markdown')
      .should('not.be.empty');
  });

  it('should reset textarea height after sending a multi-line message', () => {
    // Mock the chat API to avoid consuming AI credits
    cy.intercept('POST', '**/message/message', {
      statusCode: 200,
      headers: { 'content-type': 'text/plain' },
      body: 'Resposta mock'
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