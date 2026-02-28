import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import enUS from './locales/en-US.json';
import esES from './locales/es-ES.json';
import ptBR from './locales/pt-BR.json';

const resources = {
  'pt-BR': {
    translation: ptBR,
  },
  'es-ES': {
    translation: esES,
  },
  'en-US': {
    translation: enUS,
  },
};

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'pt-BR',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

// Map short language codes to full locales
i18n.on('languageChanged', (lng) => {
  if (lng === 'pt' || lng.startsWith('pt-')) {
    if (lng !== 'pt-BR') void i18n.changeLanguage('pt-BR');
  } else if (lng === 'es' || lng.startsWith('es-')) {
    if (lng !== 'es-ES') void i18n.changeLanguage('es-ES');
  } else if (lng === 'en' || lng.startsWith('en-')) {
    if (lng !== 'en-US') void i18n.changeLanguage('en-US');
  }
});

export default i18n;
