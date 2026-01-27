import { ComponentFixture } from '@angular/core/testing';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

/**
 * Helper para simplificar testes de componentes
 */
export class ComponentTestHelper {
  constructor(private fixture: ComponentFixture<any>) {}

  /**
   * Encontra elemento por selector
   */
  findByCss(selector: string): DebugElement | null {
    return this.fixture.debugElement.query(By.css(selector));
  }

  /**
   * Encontra todos os elementos por selector
   */
  findAllByCss(selector: string): DebugElement[] {
    return this.fixture.debugElement.queryAll(By.css(selector));
  }

  /**
   * Encontra elemento por diretiva
   */
  findByDirective(directiveType: any): DebugElement | null {
    return this.fixture.debugElement.query(By.directive(directiveType));
  }

  /**
   * Dispara evento de clique em elemento
   */
  click(selector: string): void {
    const element = this.findByCss(selector);
    if (!element) {
      throw new Error(`Element not found: ${selector}`);
    }
    element.nativeElement.click();
    this.fixture.detectChanges();
  }

  /**
   * Preenche input com valor
   */
  setInputValue(selector: string, value: string): void {
    const element = this.findByCss(selector) as DebugElement;
    if (!element) {
      throw new Error(`Input not found: ${selector}`);
    }
    const input = element.nativeElement as HTMLInputElement;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    input.dispatchEvent(new Event('change'));
    this.fixture.detectChanges();
  }

  /**
   * Verifica se elemento existe
   */
  hasElement(selector: string): boolean {
    return this.findByCss(selector) !== null;
  }

  /**
   * Verifica conteúdo de texto
   */
  getTextContent(selector: string): string {
    const element = this.findByCss(selector);
    return element ? element.nativeElement.textContent.trim() : '';
  }

  /**
   * Verifica se elemento contém classe
   */
  hasClass(selector: string, className: string): boolean {
    const element = this.findByCss(selector);
    return element ? element.nativeElement.classList.contains(className) : false;
  }

  /**
   * Dispara evento customizado
   */
  triggerEvent(selector: string, eventType: string, eventData?: any): void {
    const element = this.findByCss(selector);
    if (!element) {
      throw new Error(`Element not found: ${selector}`);
    }
    const event = new CustomEvent(eventType, { detail: eventData });
    element.nativeElement.dispatchEvent(event);
    this.fixture.detectChanges();
  }

  /**
   * Aguarda por uma condição
   */
  async waitFor(predicate: () => boolean, timeoutMs: number = 1000): Promise<void> {
    const startTime = Date.now();

    while (!predicate()) {
      if (Date.now() - startTime > timeoutMs) {
        throw new Error(`Timeout waiting for condition after ${timeoutMs}ms`);
      }
      await new Promise(resolve => setTimeout(resolve, 10));
      this.fixture.detectChanges();
    }
  }

  /**
   * Detecta mudanças e aguarda estabilidade
   */
  async stabilize(): Promise<void> {
    this.fixture.detectChanges();
    await this.fixture.whenStable();
  }
}
