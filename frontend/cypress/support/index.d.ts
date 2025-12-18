declare namespace Cypress {
  interface Chainable {
    /**
     * Custom command to log in a user through the UI.
     * Caches the session for subsequent tests.
     * @param email The user's email
     * @param password The user's password
     */
    login(email: string, password: string): Chainable<void>;
  }
}
