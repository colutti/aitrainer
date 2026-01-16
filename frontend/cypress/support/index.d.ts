declare namespace Cypress {
  interface Chainable {
    /**
     * Custom command to log in a user through the UI.
     * Caches the session for subsequent tests.
     * @param email The user's email
     * @param password The user's password
     */
    login(email: string, password: string): Chainable<void>;
    
    /**
     * Custom command to log in a user via API request.
     * @param email The user's email
     * @param password The user's password
     */
    loginDirect(email: string, password: string): Chainable<void>;
    
    /**
     * Custom command to set a properly structured fake JWT token in localStorage.
     * This prevents backend "Not enough segments" errors during mocked tests.
     */
    setFakeJWT(): Chainable<void>;
  }
}
