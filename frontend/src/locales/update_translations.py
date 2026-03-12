import json
import os

locales_dir = "/home/colutti/projects/personal/frontend/src/locales"

plans_en = {
  "free": {
    "name": "Free",
    "description": "To try out the platform",
    "button": "Get Started Free",
    "features": [
      "Access to all AI trainers",
      "Workouts and Analytics",
      "20 messages total"
    ]
  },
  "basic": {
    "name": "Basic",
    "description": "For serious starters",
    "button": "Coming Soon",
    "features": [
      "Access to all AI trainers",
      "Workouts and Analytics",
      "100 messages per month"
    ]
  },
  "pro": {
    "name": "Pro",
    "description": "For consistent results",
    "button": "Coming Soon",
    "features": [
      "Access to all AI trainers",
      "Workouts and Analytics",
      "300 messages per month"
    ]
  },
  "premium": {
    "name": "Premium",
    "description": "For athletes wanting proactive AI",
    "button": "Coming Soon",
    "features": [
      "Access to all AI trainers",
      "Workouts and Analytics",
      "1000 messages per month"
    ]
  }
}

plans_pt = {
  "free": {
    "name": "Gratuito",
    "description": "Para conhecer a plataforma",
    "button": "Começar Grátis",
    "features": [
      "Acesso a todos os treinadores",
      "Treinos e Análises",
      "20 mensagens no total"
    ]
  },
  "basic": {
    "name": "Basic",
    "description": "Para quem quer iniciar seriamente",
    "button": "Em Breve",
    "features": [
      "Acesso a todos os treinadores",
      "Treinos e Análises",
      "100 mensagens por mês"
    ]
  },
  "pro": {
    "name": "Pro",
    "description": "Para resultados consistentes",
    "button": "Em Breve",
    "features": [
      "Acesso a todos os treinadores",
      "Treinos e Análises",
      "300 mensagens por mês"
    ]
  },
  "premium": {
    "name": "Premium",
    "description": "Para atletas mais exigentes",
    "button": "Em Breve",
    "features": [
      "Acesso a todos os treinadores",
      "Treinos e Análises",
      "1000 mensagens por mês"
    ]
  }
}

plans_es = {
  "free": {
    "name": "Gratis",
    "description": "Para probar la plataforma",
    "button": "Empezar Gratis",
    "features": [
      "Acceso a todos los entrenadores IA",
      "Entrenamientos y Análisis",
      "20 mensajes en total"
    ]
  },
  "basic": {
    "name": "Básico",
    "description": "Para quien quiere empezar en serio",
    "button": "Próximamente",
    "features": [
      "Acceso a todos los entrenadores IA",
      "Entrenamientos y Análisis",
      "100 mensajes por mes"
    ]
  },
  "pro": {
    "name": "Pro",
    "description": "Para resultados consistentes",
    "button": "Próximamente",
    "features": [
      "Acceso a todos los entrenadores IA",
      "Entrenamientos y Análisis",
      "300 mensajes por mes"
    ]
  },
  "premium": {
    "name": "Premium",
    "description": "Para atletas más exigentes",
    "button": "Próximamente",
    "features": [
      "Acceso a todos los entrenadores IA",
      "Entrenamientos y Análisis",
      "1000 mensajes por mes"
    ]
  }
}

mapping = {
    "en-US.json": (plans_en, "/month", "/total", "Choose your plan", "Flexible plans for everyone. Cancel at any time.", "Recommended"),
    "pt-BR.json": (plans_pt, "/mês", "/total", "Escolha seu Plano", "Planos flexíveis para todos. Cancele quando quiser.", "Recomendado"),
    "es-ES.json": (plans_es, "/mes", "/total", "Elige tu Plan", "Planes flexibles para todos. Cancela cuando quieras.", "Recomendado")
}

for filename, (items, per_month, total, title, subtitle, restr) in mapping.items():
    filepath = os.path.join(locales_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "landing" not in data: data["landing"] = {}
    if "plans" not in data["landing"]: data["landing"]["plans"] = {}
    
    data["landing"]["plans"]["items"] = items
    data["landing"]["plans"]["per_month"] = per_month
    data["landing"]["plans"]["total"] = total
    data["landing"]["plans"]["title"] = title
    data["landing"]["plans"]["subtitle"] = subtitle
    data["landing"]["plans"]["recommended"] = restr
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated translations without fake features")
