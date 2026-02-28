import json
import os

locales_dir = "/home/colutti/projects/personal/frontend/src/locales"

replacements = {
    "en-US.json": {
        "trial_desc": "Start with 20 free messages. No commitment.",
        "trial": "Start with 20 free messages. Try it now.",
        "vision_title": "Workout & Diet Analysis",
        "vision_desc": "We analyze your training history and nutrition patterns to provide accurate progress adjustments."
    },
    "pt-BR.json": {
        "trial_desc": "Comece com 20 mensagens grátis. Sem compromisso.",
        "trial": "Comece com 20 mensagens grátis. Teste agora.",
        "vision_title": "Análise de Treino e Dieta",
        "vision_desc": "Analisamos seu histórico de treinos e alimentação para ajustar seu progresso com precisão."
    },
    "es-ES.json": {
        "trial_desc": "Comienza con 20 mensajes gratis. Sin compromiso.",
        "trial": "Comienza con 20 mensajes gratis. Pruébalo ahora.",
        "vision_title": "Análisis de Entrenamiento y Dieta",
        "vision_desc": "Analizamos tu historial de entrenamiento y alimentación para ajustar tu progreso con precisión."
    }
}

for filename, texts in replacements.items():
    filepath = os.path.join(locales_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Update hero trial desc
    if "landing" in data and "hero" in data["landing"]:
        data["landing"]["hero"]["trial_desc"] = texts["trial_desc"]
        
    # Update cta trial desc
    if "landing" in data and "cta" in data["landing"]:
        data["landing"]["cta"]["trial"] = texts["trial"]
        
    # Update vision differentiator
    if "landing" in data and "diff" in data["landing"] and "features" in data["landing"]["diff"] and "vision" in data["landing"]["diff"]["features"]:
        data["landing"]["diff"]["features"]["vision"]["title"] = texts["vision_title"]
        data["landing"]["diff"]["features"]["vision"]["description"] = texts["vision_desc"]
        
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("Updates applied successfully")
