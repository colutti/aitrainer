describe('Chat Bugs Reproduction', () => {
  beforeEach(() => {
    // Essential startup intercepts for Dashboard
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', {
      statusCode: 200,
      body: [
          {
            sender: 'ai',
            text: 'Olá! Como posso ajudar hoje?',
            timestamp: new Date().toISOString()
          }
      ]
    }).as('chatHistory');
    cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
    cy.intercept('GET', '**/workout/stats', { body: { streak: 0, frequency: [] } }).as('getWorkoutStats');
    cy.intercept('GET', '**/nutrition/stats', { body: { daily_target: 2000, current_macros: {} } }).as('getNutritionStats');

    // Bypass UI login
    cy.visit('/', {
        onBeforeLoad: (win) => {
            win.localStorage.setItem('jwt_token', 'fake-jwt-token');
        }
    });

    // Wait for app to be ready and navigate to chat
    cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
    cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
    
    cy.contains('button', 'Chat').click({ force: true });
    cy.get('app-chat', { timeout: 10000 }).should('be.visible');
  });

  it('Bug 1: Should show ONLY "Digitando" bubble (not an extra timestamp bubble) while AI is responding', () => {
    // Mock the message endpoint with a delay
    cy.intercept('POST', '**/message/message', {
      delay: 5000, 
      body: 'Response',
      headers: { 'content-type': 'text/plain' }
    }).as('slowMessage');

    // Send a message
    cy.get('textarea[name="newMessage"]').type('Hello');
    cy.get('button[type="submit"]').click();

    // Wait a moment for the message to be processed and signals updated
    cy.wait(500);

    // Assert bubbles
    // 1. User message ("Hello") - justify-end
    // 2. Typing indicator ("Digitando") - justify-start (inside the typing block)
    // 3. Welcome message ("Olá") - justify-start
    
    // The "Digitando" is NOT in a .justify-start block that contains reversedMessages by default?
    // Let's check the template again.
    
    /*
      @if (isTyping()) {
      <div class="flex justify-start animate-slide-in-fade">
        <div ...>
          <span>Digitando</span>
    */
    
    // Yes it is.
    
    cy.get('.justify-start').then(($leftBubbles) => {
      const texts = [...$leftBubbles].map(el => el.innerText.trim());
      cy.log(`Found left bubbles: ${JSON.stringify(texts)}`);
      
      // Should find at least "Digitando" and "Olá"
      expect(texts.some(t => t.includes('Digitando'))).to.be.true;
      expect(texts.some(t => t.includes('Olá'))).to.be.true;
      
      // Check for empty AI bubbles (the bug where a new empty AI message with timestamp appeared)
      const emptyBubbles = [...$leftBubbles].filter(el => {
          const text = el.innerText.trim();
          // Filter out "Digitando" bubble and the welcome message
          return !text.includes('Digitando') && !text.includes('Olá') && text.length > 0;
      });
      
      // If there's an empty bubble with just timestamp, it shouldn't show up yet or it should be "clean".
      // Our Current Implementation for sendMessage:
      /*
        const aiMessage: Message = { id: aiMessageId, text: '', sender: 'ai', ... };
        this.messages.update((msgs) => [...msgs, aiMessage]);
      */
      // And in template:
      /*
        @if (message.text && message.text.trim().length > 0 || message.sender === 'user') {
      */
      // This @if prevents showing empty AI messages.
      
      // So we should NOT see the empty AI bubble.
      expect(emptyBubbles.length).to.eq(0, `Found unexpected AI bubbles: ${JSON.stringify(emptyBubbles.map(e => e.innerText))}`);
    });
  });

  it('Bug 2: Scroll button should NOT appear when already at bottom', () => {
    // Mock fast responses
    cy.intercept('POST', '**/message/message', {
      body: 'Short reply',
      headers: { 'content-type': 'text/plain' }
    }).as('msg');

    // Send multiple messages to create scrollable content
    for (let i = 0; i < 5; i++) {
      cy.get('textarea[name="newMessage"]').type(`Message ${i}`);
      cy.get('button[type="submit"]').click();
      cy.wait('@msg');
      cy.wait(200); 
    }

    // Ensure we're at the bottom
    cy.get('.chat-scroll-container').scrollTo('bottom');
    cy.wait(500);

    // Scroll button should not exist when at bottom
    // The button has classes: fixed, bg-primary
    cy.get('button.fixed.bg-primary').should('not.exist');
  });
});
