/**
 * Aggregate exports for all mocks
 * Makes it easier for tests to import from a single location
 */

export { COMMON_MOCKS, setupCommonIntercepts } from './intercepts';
export { ERROR_MOCKS, createErrorResponse, createValidationError } from './mocks/error.mocks';
export { CHAT_MOCKS } from './mocks/chat.mocks';
export { ONBOARDING_MOCKS } from './mocks/onboarding.mocks';
