import { COMMON_MOCKS } from '../support/mocks';

/**
 * SKIPPED: Create workout route not implemented
 * Workout creation is handled via the workout-drawer component in workouts view.
 * The app uses signals-based navigation, see workouts.component.ts
 */
describe.skip('Create Workout Flow', () => {
  beforeEach(() => {
    cy.mockLogin();
    // Navigate using NavigationService
    // cy.navigateTo('workouts'); // Drawer opens within the view
  });

  it('should create workout with exercises', () => {
    cy.intercept('POST', '**/workout', { body: { id: '123', date: new Date().toISOString(), exercises: [] } }).as(
      'createWorkout'
    );

    cy.get('input[name="workoutType"]').type('Peito');
    cy.get('input[name="duration"]').type('60');

    // Add exercise
    cy.get('button').contains('Adicionar Exercício').click();
    cy.get('input[name="exerciseName"]').type('Supino');
    cy.get('input[name="reps"]').type('10');
    cy.get('input[name="weight"]').type('100');
    cy.get('button').contains('Salvar Exercício').click();

    cy.get('button').contains('Salvar Treino').click();
    cy.wait('@createWorkout');

    cy.url().should('include', '/workouts');
  });

  it('should validate required fields', () => {
    cy.get('button').contains('Salvar Treino').should('be.disabled');

    cy.get('input[name="workoutType"]').type('Peito');
    cy.get('button').contains('Salvar Treino').should('be.disabled');
  });

  it('should add multiple exercises', () => {
    cy.intercept('POST', '**/workout', { body: { id: '123', exercises: [] } }).as('createWorkout');

    cy.get('input[name="workoutType"]').type('Peito');
    cy.get('input[name="duration"]').type('60');

    // Add 3 exercises
    for (let i = 0; i < 3; i++) {
      cy.get('button').contains('Adicionar Exercício').click();
      cy.get('input[name="exerciseName"]').type(`Exercício ${i}`);
      cy.get('input[name="reps"]').type('10');
      cy.get('input[name="weight"]').type('50');
      cy.get('button').contains('Salvar Exercício').click();
    }

    cy.get('[data-test="exercise-row"]').should('have.length', 3);
  });

  it('should delete exercise before saving', () => {
    cy.get('input[name="workoutType"]').type('Peito');
    cy.get('input[name="duration"]').type('60');

    cy.get('button').contains('Adicionar Exercício').click();
    cy.get('input[name="exerciseName"]').type('Supino');
    cy.get('input[name="reps"]').type('10');
    cy.get('input[name="weight"]').type('100');
    cy.get('button').contains('Salvar Exercício').click();

    cy.get('[data-test="delete-exercise"]').click();
    cy.get('[data-test="exercise-row"]').should('not.exist');
  });

  it('should show loading state while saving', () => {
    cy.intercept('POST', '**/workout', { delay: 1000, body: { id: '123' } }).as('createWorkoutSlow');

    cy.get('input[name="workoutType"]').type('Peito');
    cy.get('input[name="duration"]').type('60');
    cy.get('button').contains('Adicionar Exercício').click();
    cy.get('input[name="exerciseName"]').type('Supino');
    cy.get('input[name="reps"]').type('10');
    cy.get('button').contains('Salvar Exercício').click();

    cy.get('button').contains('Salvar Treino').click();
    cy.get('[data-test="loading-spinner"]').should('be.visible');
  });

  it('should validate numeric fields', () => {
    cy.get('input[name="duration"]').type('abc');
    cy.get('button').contains('Salvar Treino').should('be.disabled');
  });
});
