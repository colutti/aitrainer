const fs = require('fs');
const path = require('path');

const localesDir = path.join(__dirname, 'locales');
const files = fs.readdirSync(localesDir).filter(f => f.endsWith('.json'));

const plansPtBR = {
  free: {
    name: "Gratuito",
    description: "Para conhecer a plataforma",
    button: "Começar Grátis",
    features: [
      "20 mensagens no total",
      "Todos os treinadores"
    ]
  },
  basic: {
    name: "Basic",
    description: "Para quem quer iniciar seriamente",
    button: "Em Breve",
    features: [
      "100 mensagens por mês",
      "Histórico guardado",
      "Todos os treinadores"
    ]
  },
  pro: {
    name: "Pro",
    description: "Para resultados consistentes",
    button: "Em Breve",
    features: [
      "300 mensagens por mês",
      "Histórico ilimitado",
      "Todos os treinadores"
    ]
  },
  premium: {
    name: "Premium",
    description: "Para atletas que querem ter a IA proativamente em cima",
    button: "Em Breve",
    features: [
      "1000 mensagens por mês",
      "Resumo dinâmico",
      "Acesso antecipado a features"
    ]
  }
};

// Simplified translation approach - we'll just use English and Portuguese, and default to Portuguese for others.
const plansEn = {
  free: {
    name: "Free",
    description: "To try out the platform",
    button: "Get Started Free",
    features: [
      "20 total messages",
      "All AI trainers"
    ]
  },
  basic: {
    name: "Basic",
    description: "For serious starters",
    button: "Coming Soon",
    features: [
      "100 messages per month",
      "History saved",
      "All AI trainers"
    ]
  },
  pro: {
    name: "Pro",
    description: "For consistent results",
    button: "Coming Soon",
    features: [
      "300 messages per month",
      "Unlimited history saved",
      "All AI trainers"
    ]
  },
  premium: {
    name: "Premium",
    description: "For athletes wanting proactive AI",
    button: "Coming Soon",
    features: [
      "1000 messages per month",
      "Dynamic summaries",
      "Early features access"
    ]
  }
};


for (const file of files) {
  const filePath = path.join(localesDir, file);
  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  
  if (!data.landing) data.landing = {};
  if (!data.landing.plans) data.landing.plans = {};
  
  // Update translation obj
  const plans = file === 'en.json' ? plansEn : plansPtBR;
  data.landing.plans.items = plans;
  
  if (file === 'en.json') {
      data.landing.plans.per_month = "/month";
      data.landing.plans.total = "/total";
      data.landing.plans.title = "Choose your plan";
      data.landing.plans.subtitle = "Flexible plans for everyone. Cancel at any time.";
  } else {
      data.landing.plans.per_month = "/mês";
      data.landing.plans.total = "/total";
      data.landing.plans.title = "Escolha seu Plano";
      data.landing.plans.subtitle = "Planos flexíveis para todos. Cancele quando quiser.";
  }
  
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}
console.log('Done modifying locales');
