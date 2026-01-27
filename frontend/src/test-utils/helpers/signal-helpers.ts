import { Signal, computed, signal, effect } from '@angular/core';

/**
 * Helper para testar signals em testes Jest
 * Usa flush para processar efeitos de forma síncrona
 */
export class SignalTestHelper {
  /**
   * Cria um signal de teste que pode ser modificado
   */
  static createTestSignal<T>(initialValue: T): Signal<T> {
    return signal(initialValue);
  }

  /**
   * Verifica se um sinal mudou após uma operação
   */
  static expectSignalChange<T>(
    sig: Signal<T>,
    expectedValue: T,
    operation: () => void
  ): void {
    const oldValue = sig();
    operation();
    expect(sig()).not.toEqual(oldValue);
    expect(sig()).toEqual(expectedValue);
  }

  /**
   * Cria um computed signal de teste
   */
  static createComputedSignal<T>(
    deps: Signal<any>[],
    computation: () => T
  ): Signal<T> {
    return computed(computation);
  }

  /**
   * Rastreia todas as mudanças de um sinal
   */
  static trackSignalChanges<T>(sig: Signal<T>): T[] {
    const changes: T[] = [];
    effect(() => {
      changes.push(sig());
    });
    return changes;
  }

  /**
   * Aguarda uma mudança de sinal (com timeout)
   */
  static async waitForSignalChange<T>(
    sig: Signal<T>,
    predicate: (value: T) => boolean,
    timeoutMs: number = 1000
  ): Promise<T> {
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (predicate(sig())) {
          clearInterval(checkInterval);
          resolve(sig());
        }

        if (Date.now() - startTime > timeoutMs) {
          clearInterval(checkInterval);
          reject(new Error(`Signal did not meet predicate within ${timeoutMs}ms`));
        }
      }, 10);
    });
  }
}
