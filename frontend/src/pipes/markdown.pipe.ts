import { Pipe, PipeTransform, SecurityContext } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

/**
 * Pipe to convert markdown text to safe HTML.
 * 
 * This pipe uses the 'marked' library to parse markdown and Angular's
 * DomSanitizer to ensure the resulting HTML is safe from XSS attacks.
 * 
 * Usage in templates:
 * ```html
 * <div [innerHTML]="markdownText | markdown"></div>
 * ```
 */
@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  /**
   * Transforms markdown text into sanitized HTML.
   * 
   * @param value - The markdown text to convert
   * @returns Sanitized HTML that is safe to render
   */
  transform(value: string): SafeHtml {
    if (!value) {
      return '';
    }

    // Convert markdown to HTML
    const html = marked.parse(value, { async: false }) as string;
    
    // Sanitize HTML to prevent XSS attacks
    const sanitized = this.sanitizer.sanitize(SecurityContext.HTML, html);
    
    return sanitized || '';
  }
}
