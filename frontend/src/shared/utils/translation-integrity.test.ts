import { describe, it } from 'vitest';

import enUS from '../../locales/en-US.json';
import esES from '../../locales/es-ES.json';
import ptBR from '../../locales/pt-BR.json';

/**
 * Esse teste garante a paridade estrutural entre os arquivos JSON.
 * Ignoramos a varredura de código fonte neste momento para evitar falsos positivos de testes.
 */
describe('i18n Dictionary Parity', () => {
  it('should have consistent keys across all translation files', () => {
    const checkKeys = (source: any, target: any, lang: string, path = '') => {
      Object.keys(source).forEach((key) => {
        const currentPath = path ? `${path}.${key}` : key;
        if (target[key] === undefined) {
          throw new Error(`Key "${currentPath}" exists in source but is missing in ${lang}`);
        }
        if (typeof source[key] === 'object' && source[key] !== null && !Array.isArray(source[key])) {
          checkKeys(source[key], target[key], lang, currentPath);
        }
      });
    };

    // Compara todos contra todos para garantir simetria total
    checkKeys(ptBR, enUS, 'en-US');
    checkKeys(ptBR, esES, 'es-ES');
    
    checkKeys(enUS, ptBR, 'pt-BR');
    checkKeys(enUS, esES, 'es-ES');

    checkKeys(esES, ptBR, 'pt-BR');
    checkKeys(esES, enUS, 'en-US');
  });
});
