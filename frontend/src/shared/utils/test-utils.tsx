import { render as rtlRender } from '@testing-library/react';
import i18n from 'i18next';
import { initReactI18next, I18nextProvider } from 'react-i18next';
import { MemoryRouter } from 'react-router-dom';

// @ts-expect-error - JSON module resolution
import ptBR from '../locales/pt-BR.json';

 
const resources = {
  'pt-BR': {
    translations: ptBR as Record<string, unknown>
  }
};

// Inicializa o i18n para os testes com o JSON real
void i18n.use(initReactI18next).init({
  lng: 'pt-BR',
  fallbackLng: 'pt-BR',
  ns: ['translations'],
  defaultNS: 'translations',
  debug: false,
  resources
});

export function render(ui: React.ReactElement, { route = '/' } = {}) {
  return rtlRender(
    <I18nextProvider i18n={i18n}>
      <MemoryRouter initialEntries={[route]}>
        {ui}
      </MemoryRouter>
    </I18nextProvider>
  );
}

// Re-exporta tudo do testing-library individualmente ou conforme necessário para evitar erro de Fast Refresh
export { screen, fireEvent, waitFor, act, cleanup } from '@testing-library/react';
