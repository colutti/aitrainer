describe('Chat Bugs Reproduction', () => {
  beforeEach(() => {
    // Mock all API calls
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt' }
    }).as('login');

    cy.intercept('GET', '**/message/history*', {
      statusCode: 200,
      body: [] // Empty history
    }).as('getHistory');

    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    
    cy.intercept('GET', '**/trainer/trainer_profile', {
      statusCode: 200,
      body: { trainer_type: 'atlas' }
    }).as('trainerProfile');

    cy.intercept('GET', '**/trainer/available_trainers', {
      statusCode: 200,
      body: [{ trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' }]
    }).as('availableTrainers');

    // Login
    cy.login('cypress_user@test.com', 'Password123');
    
    // Navigate to chat
    cy.get('button').contains('Chat').click();
    cy.wait('@getHistory');
  });

  it('Bug 1: Should show ONLY "Digitando" bubble (not an extra timestamp bubble) while AI is responding', () => {
    // Mock the message endpoint with a delay to keep it in "typing" state
    cy.intercept('POST', '**/message/message', {
      delay: 10000, // Long delay to observe typing state
      body: 'Response',
      headers: { 'content-type': 'text/plain' }
    }).as('slowMessage');

    // Send a message
    cy.get('textarea[name="newMessage"]').type('Hello');
    cy.get('button[type="submit"]').click();

    // Wait a moment for the message to be processed
    cy.wait(500);

    // CRITICAL ASSERTION:
    // Inside the chat scroll container, we should have:
    // 1. User message ("Hello") - blue bubble on the right (justify-end)
    // 2. Typing indicator ("Digitando") - gray bubble on the left (justify-start)
    // 3. Welcome message ("Olá!") - gray bubble on the left (justify-start)
    // 
    // We should NOT have an empty AI bubble with just a timestamp.
    
    // Count AI-style bubbles (left-aligned gray bubbles in the chat area)
    cy.get('.chat-scroll-container .justify-start').then(($leftBubbles) => {
      // Expected: Welcome message + Typing indicator = 2
      // If bug exists: Welcome + Typing + Empty timestamp bubble = 3
      const count = $leftBubbles.length;
      
      // Verify the content of each bubble
      const texts = [...$leftBubbles].map(el => el.innerText.trim());
      
      // Log for debugging
      cy.log(`Found ${count} left-aligned bubbles: ${JSON.stringify(texts)}`);
      
      // There should be exactly 2 left bubbles
      expect(count).to.eq(2, 
        `Expected 2 left bubbles (Welcome + Digitando), but found ${count}: ${JSON.stringify(texts)}`
      );
      
      // One should contain "Digitando"
      expect(texts.some(t => t.includes('Digitando'))).to.be.true;
      
      // One should contain "Olá" (welcome message)
      expect(texts.some(t => t.includes('Olá'))).to.be.true;
    });
    
    // Also verify the user message appears
    cy.get('.chat-scroll-container .justify-end').should('contain.text', 'Hello');
  });

  it('Bug 2: Scroll button should NOT appear when already at bottom', () => {
    // Mock fast responses
    cy.intercept('POST', '**/message/message', {
      body: 'Short reply',
      headers: { 'content-type': 'text/plain' }
    }).as('msg');

    // Send multiple messages to create scrollable content
    for (let i = 0; i < 8; i++) {
      cy.get('textarea[name="newMessage"]').type(`Message ${i}`);
      cy.get('button[type="submit"]').click();
      cy.wait('@msg');
      cy.wait(200); // Brief pause
    }

    // Ensure we're at the bottom by scrolling there
    cy.get('.chat-scroll-container').scrollTo('bottom');
    
    // Wait for scroll event to be processed
    cy.wait(500);

    // The scroll button should NOT be visible when at bottom
    // The button has classes: fixed, bottom-24, bg-primary
    cy.get('.chat-scroll-container').parent().within(() => {
      // Button should not exist when at bottom
      cy.get('button.fixed.bg-primary').should('not.exist');
    });
  });
});
