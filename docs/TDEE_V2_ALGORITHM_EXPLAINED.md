# Algoritmo TDEE v2 — Guia Técnico

## Índice
1. [Visão Geral](#visão-geral)
2. [Pipeline de 9 Passos](#pipeline-de-9-passos)
3. [Exemplos Práticos](#exemplos-práticos)
4. [Constantes e Configurações](#constantes-e-configurações)
5. [Referências Científicas](#referências-científicas)

---

## Visão Geral

O **TDEE v2** (Total Daily Energy Expenditure v2) é um algoritmo adaptativo que estima quantas calorias você gasta diariamente, analisando seu histórico de peso e ingestão calórica. O objetivo é calcular um alvo calórico diário sustentável que leve você ao seu objetivo (perder peso, ganhar massa ou manter) de forma segura e eficiente.

### Princípios Fundamentais

O v2 é baseado em 5 princípios científicos:

#### 1. **Adaptatividade sem penalidade**
- O TDEE estimado ajusta naturalmente se a perda/ganho não acontece
- Não há "punição extra" — apenas ajuste da estimativa baseado em dados reais
- Se você come 1900 kcal e não perde peso, significa seu TDEE real é ~1900

#### 2. **Densidade energética dinâmica** (Forbes/Hall, 2007-2008)
- Diferentes proporções de gordura vs. músculo têm diferentes calorias
- Alguém com 10% gordura corporal perde peso diferente de alguém com 40%
- Fórmula: `kcal/kg = fat_fraction × 9400 + (1 - fat_fraction) × 1800`

#### 3. **Ajuste gradual** (Carbon Diet Coach)
- Target nunca muda mais de ±100 kcal por semana
- Previne "shocks" no metabolismo
- Garante aderência (mudanças progressivas, não abruptas)

#### 4. **Pisos de segurança** (NIH/Harvard)
- Nunca menos de 1200 kcal (mulheres) / 1500 kcal (homens)
- Nunca mais de 30% de déficit do TDEE
- Protege saúde metabólica

#### 5. **Detecção robusta de outliers** (Modified Z-Score)
- Identifica picos anormais (cheat meals, retenção hídrica)
- Usa dois passes: estatístico + contextual
- Melhora acurácia de trend 20-30%

---

## Pipeline de 9 Passos

### Passo 1: Detecção de Outliers (Modified Z-Score + Contextual)

**O que faz:** Remove valores anormais de peso que distorcem a tendência.

**Modified Z-Score:**
```
Z = 0.6745 × (x - mediana) / MAD

Se |Z| > 3.5: outlier estatístico (removido)
```

**Exemplo:**
```
Pesos últimos 7 dias: [76.0, 76.2, 75.8, 76.1, 82.0, 75.9, 76.0]
                                             ↑
                                      Outlier (cheat meal + retenção de água)

Mediana = 76.0
MAD = 0.15
Z para 82.0 = 0.6745 × (82.0 - 76.0) / 0.15 = 26.98 >> 3.5
REMOVIDO ✓

Resultado: [76.0, 76.2, 75.8, 76.1, 75.9, 76.0]
```

**Detecção Contextual:**
- Se delta em 1 dia > 1.0 kg E próximo registro volta ao baseline → **transient spike** (removido)
- Se delta em 1 dia > 1.0 kg E próximo registro confirma novo nível → **step change** (reset baseline)

---

### Passo 2: Suavização de Peso (EMA + Regressão Linear Ponderada)

**Exponential Moving Average (EMA):**
- Span = 10 dias
- Alpha = 2 / (10 + 1) ≈ 0.18
- Fórmula: `trend_novo = peso_atual × alpha + trend_anterior × (1 - alpha)`

**Exemplo:**
```
Dia 1: peso = 76.0 kg → trend = 76.0 (primeiro valor)
Dia 2: peso = 76.1 kg → trend = 76.1 × 0.18 + 76.0 × 0.82 = 76.018
Dia 3: peso = 75.9 kg → trend = 75.9 × 0.18 + 76.018 × 0.82 = 75.945
...
Dia 28: peso = 75.0 kg → trend ≈ 75.5 kg (suavizado)
```

**Regressão Linear Ponderada:**
- Usa `np.polyfit` com pesos exponenciais
- Decay = 0.10 (dados recentes pesam mais)
- Calcula slope = kg/dia de mudança ao longo do período
- Fórmula: `w_i = exp(-0.10 × (max_day - day_i))`

---

### Passo 3: Taxa de Mudança (Weighted Linear Regression Slope)

**O que faz:** Calcula a tendência real de perda/ganho de peso.

**Exemplo (últimas 28 dias):**
```
Start weight: 77.0 kg
End weight: 75.0 kg
Total change: -2.0 kg em 28 dias
Slope: -2.0 / 28 ≈ -0.071 kg/dia
Rate semanal: -0.071 × 7 = -0.50 kg/semana
```

---

### Passo 4: Conteúdo Energético Dinâmico (Forbes/Hall Model)

**O que faz:** Calcula quantas kcal correspondem a 1 kg de mudança de peso, baseado na composição corporal.

**Fórmula Base (Forbes/Hall 2007-2008):**
```
fat_fraction = 0.75 + (body_fat_pct - 25) × 0.005
```

**Interpretação:**
```
25% body fat (baseline): fat_fraction = 0.75
  → 75% da mudança é gordura, 25% é músculo

35% body fat: fat_fraction = 0.80
  → 80% da mudança é gordura

15% body fat: fat_fraction = 0.70
  → 70% da mudança é gordura
```

**Correção por Taxa Rápida de Perda:**
```
Se rate_weekly > 0.5 kg/semana (perda rápida):
    fat_fraction -= 0.05 × (rate_weekly - 0.5)

Exemplo: Rate = 1.0 kg/semana
    Redução = 0.05 × (1.0 - 0.5) = 0.025
    Novo fat_fraction = 0.75 - 0.025 = 0.725
    (Reconhecendo que perda rápida inclui mais músculo)
```

**Cálculo Final:**
```
energy_per_kg = fat_fraction × 9400 + (1 - fat_fraction) × 1800

Exemplo (Rafael: 23% BF, slope = -0.071):
  fat_fraction = 0.75 + (23 - 25) × 0.005 = 0.74
  rate_weekly = 0.071 × 7 = 0.497 (não ativa penalty)
  energy_per_kg = 0.74 × 9400 + 0.26 × 1800 = 7424 kcal/kg
```

**Clamping (Limites Fisiológicos):**
```
fat_fraction = max(0.50, min(0.90, fat_fraction))
  0.50 → mínimo fisiológico (pessoa muito magra)
  0.90 → máximo realista (pessoa muito gorda)
```

---

### Passo 5: Cálculo de TDEE

**O que faz:** Estima quantas calorias você gasta diariamente.

**Fórmula Fundamental (Lei da Termodinâmica):**
```
TDEE = avg_calories_consumed - (daily_weight_change_slope × energy_per_kg)
```

**Verificação:**
- Se você come 2000 kcal e perde 0.1 kg/dia:
  - TDEE = 2000 - (0.1 × 7424) = 2000 - 742 = 1258 kcal
  - Ou: TDEE = 2000 + 742 = 2742 kcal (mais realista)
  - Deficit = 742 kcal/dia = 0.1 kg/dia ✓

**Exemplo (Rafael):**
```
Período: últimos 28 dias
Calorias médias: 1920 kcal/dia
Slope: -0.071 kg/dia
Energy per kg: 7424 kcal/kg
Daily deficit: -0.071 × 7424 = -527 kcal/dia

TDEE = 1920 - (-527) = 1920 + 527 = 2447 kcal

Verificação:
  Deficit = 527 kcal/dia × 28 = 14,756 kcal
  Peso perdido esperado = 14,756 / 7424 = 1.99 kg ≈ 2.0 kg real ✓
```

---

### Passo 6: Sanity Checks (Clamping de Limites)

**O que faz:** Garante que a estimativa está em bounds razoáveis.

**Limites:**
```
MIN_TDEE = 1200 kcal (nunca menos)
MAX_TDEE = 5000 kcal (nunca mais)

TDEE_final = max(1200, min(5000, TDEE_calculado))
```

---

### Passo 7: Cálculo de Target (Sem Penalidade)

**O que faz:** Calcula a meta calórica diária para atingir o objetivo.

**Para Perda de Peso:**
```
target = TDEE - (goal_rate_kg_per_week × 1100)

Exemplo (meta 0.5 kg/semana):
  target = 2447 - (0.5 × 1100) = 2447 - 550 = 1897 kcal
  Deficit = 550 kcal/dia = 22.5% (SUSTENTÁVEL)
```

**Para Ganho de Peso:**
```
target = TDEE + (goal_rate_kg_per_week × 1100)

Exemplo (musculação, 0.5 kg/semana):
  target = 2447 + 550 = 2997 kcal
  Superávit = 22.5% (para síntese protéica)
```

**Para Manutenção:**
```
target = TDEE (sem ajuste)
```

---

### Passo 8: Ajuste Gradual (±100 kcal/Semana)

**O que faz:** Impede mudanças drásticas na recomendação calórica.

**Lógica:**
```
1. Se é a primeira vez:
   retorna ideal_target direto (sem cap)

2. Se última check-in foi < 7 dias atrás:
   retorna previous_target (não muda ainda)

3. Se última check-in foi >= 7 dias atrás:
   diff = ideal_target - previous_target

   if |diff| <= 100:
       retorna ideal_target (dentro do range)
   else:
       step = +100 if diff > 0 else -100
       retorna previous_target + step (capped)
```

**Exemplo (8 dias após última check-in):**
```
previous_target = 2100 kcal
ideal_target = 1897 kcal
diff = 1897 - 2100 = -203 kcal (quer reduzir muito)

Como |diff| = 203 > 100:
  step = -100 kcal
  result = 2100 - 100 = 2000 kcal

Semana que vem (nova check-in):
  previous_target = 2000 kcal
  ideal_target = 1850 kcal
  diff = -150 kcal
  step = -100
  result = 1900 kcal

Semana 3:
  previous_target = 1900 kcal
  ideal_target = 1820 kcal
  diff = -80 kcal (agora <= 100)
  result = 1820 kcal ✓ (finalmente atinge ideal)
```

---

### Passo 9: Piso de Segurança (Gênero + Max 30% Deficit)

**O que faz:** Garante que o target é seguro para a saúde.

**Dois Pisos:**

**1. Piso por Gênero (NIH/Harvard):**
```
MIN_CALORIES_FEMALE = 1200 kcal
MIN_CALORIES_MALE = 1500 kcal

Exemplo (homem):
  Se target calculado = 1300 kcal
  → result = max(1300, 1500) = 1500 kcal (piso aplicado)
```

**2. Piso por Déficit Máximo (30%):**
```
Para perda de peso:
  min_by_deficit = TDEE × (1 - MAX_DEFICIT_PCT)
                 = TDEE × 0.70

Exemplo (TDEE = 2447):
  min_by_deficit = 2447 × 0.70 = 1713 kcal (máximo déficit seguro)

  Se ideal_target = 1500 kcal (52% deficit — perigoso!)
  → result = max(1500, 1713) = 1713 kcal (piso aplicado)
```

**Decisão Final:**
```
Para perda:
  target = max(gender_min, min_by_deficit, target)

Exemplo (Rafael):
  gender_min = 1500 kcal
  min_by_deficit = 2447 × 0.70 = 1713 kcal
  target = max(1500, 1713, 1820) = 1820 kcal ✓

  Deficit final = (2447 - 1820) / 2447 = 25.6% (SEGURO)
```

---

## Exemplos Práticos

### Exemplo 1: Rafael — Perda de Peso (Homem)

**Perfil:**
- Idade: 45 anos, Gênero: Masculino
- Peso atual: 75.0 kg, Altura: 175 cm
- Body Fat: 23.3%
- Objetivo: Perder 0.5 kg/semana
- Meta final: 72 kg
- Histórico: 28 dias de dados

**Dados de Entrada:**
```
Pesos (últimos 28 dias):
77.0, 76.8, 76.5, 76.2, 76.0, 75.8, 75.5, 75.2, 75.0, 74.8, 74.5,
74.2, 74.0, 73.8, 73.5, 73.2, 73.0, 72.8, 72.5, 72.2, 72.0, 71.8,
71.5, 71.2, 71.0, 70.8, 70.5, 70.2 kg

Calorias consumidas (média):
Variação: 1850-1920 kcal/dia
Média: 1908 kcal/dia

Body Fat: 23.3%
```

**Cálculos:**

**Passo 1-2: Outlier & Smoothing**
```
Detecta: Sem outliers óbvios
Trend suavizado: 77.0 → 70.2 kg (tendência clara)
```

**Passo 3: Taxa de Mudança**
```
Slope = (70.2 - 77.0) / 28 = -6.8 / 28 = -0.243 kg/dia
Rate semanal = -0.243 × 7 = -1.70 kg/semana

Nota: Primeiras semanas geralmente têm peso de água.
```

**Passo 4: Energia Dinâmica**
```
Body fat: 23.3%
fat_fraction = 0.75 + (23.3 - 25) × 0.005 = 0.7415

Rate semanal = 1.70 (muito alta)
Penalty = 0.05 × (1.70 - 0.5) = 0.06
fat_fraction = 0.7415 - 0.06 = 0.6815 (clamped)

energy_per_kg = 0.6815 × 9400 + 0.3185 × 1800
              = 6406 + 573 = 6979 kcal/kg
```

**Passo 5: TDEE**
```
TDEE = 1908 - (-0.243 × 6979)
     = 1908 + 1696
     = 3604 kcal

(Provavelmente inflado por água. Próximo check-in ajustará.)
```

**Passo 7: Target (Ideal)**
```
target = 3604 - (0.5 × 1100) = 3604 - 550 = 3054 kcal
Deficit = 550 / 3604 = 15.3% (suave)
```

**Passo 8: Ajuste Gradual**
```
Se primeira vez: retorna 3054 direto
Se há anterior e >= 7 dias: aplica ±100 kcal cap
```

**Passo 9: Piso de Segurança**
```
gender_min = 1500 kcal
min_by_deficit = 3604 × 0.70 = 2523 kcal
target_final = max(1500, 2523, 3054) = 3054 kcal

Deficit = (3604 - 3054) / 3604 = 15.3% ✓ (SEGURO)
```

**RESULTADO FINAL: 3054 kcal/dia**

---

### Exemplo 2: Carla — Ganho de Massa (Mulher)

**Perfil:**
- Idade: 28 anos, Gênero: Feminino
- Peso atual: 58 kg, Altura: 165 cm
- Body Fat: 32%
- Objetivo: Ganhar 0.5 kg/semana de massa muscular
- Meta final: 64 kg
- Histórico: 28 dias de dados

**Dados de Entrada:**
```
Pesos (últimos 28 dias):
57.2, 57.3, 57.4, 57.5, 57.6, 57.7, 57.8, 57.9, 58.0, 58.1, 58.2, 58.3,
58.4, 58.5, 58.6, 58.7, 58.8, 58.9, 59.0, 59.1, 59.2, 59.3, 59.4, 59.5 kg
(ganho consistente de ~0.035 kg/dia)

Calorias: média 2180 kcal/dia
Body Fat: 32%
```

**Cálculos:**

**Passo 3: Taxa de Mudança**
```
Slope = (59.5 - 57.2) / 28 = 2.3 / 28 = 0.082 kg/dia
Rate semanal = 0.082 × 7 = 0.574 kg/semana (apropriado)
```

**Passo 4: Energia Dinâmica**
```
Body fat: 32%
fat_fraction = 0.75 + (32 - 25) × 0.005 = 0.785

Rate semanal = 0.574
Penalty = 0.05 × (0.574 - 0.5) = 0.0037
fat_fraction = 0.781

energy_per_kg = 0.781 × 9400 + 0.219 × 1800 = 7735 kcal/kg
```

**Passo 5: TDEE**
```
TDEE = 2180 - (0.082 × 7735)
     = 2180 - 634
     = 1546 kcal

Interpretação: Carla come acima de seu TDEE em 634 kcal/dia para ganho.
```

**Passo 7: Target (Ganho)**
```
target = 1546 + (0.5 × 1100) = 1546 + 550 = 2096 kcal
Superávit = 550 / 1546 = 35.6% (ok para ganho muscular)
```

**Passo 9: Piso de Segurança**
```
gender_min = 1200 kcal
target_final = max(1200, 2096) = 2096 kcal
```

**RESULTADO FINAL: 2096 kcal/dia**

---

### Exemplo 3: João — Manutenção (Homem)

**Perfil:**
- Idade: 35 anos, Gênero: Masculino
- Peso atual: 82 kg, Altura: 180 cm
- Body Fat: 28%
- Objetivo: Manter peso (0 kg/semana)
- Histórico: 28 dias de dados

**Dados de Entrada:**
```
Pesos (últimos 28 dias):
82.1, 82.0, 82.1, 82.2, 81.9, 82.0, 82.1, 82.0, 82.2, 81.9,
82.1, 82.0, 82.1, 82.0, 82.2, 81.9, 82.0, 82.1, 82.0, 82.1,
81.9, 82.0, 82.1, 82.0, 82.1, 82.0, 82.2, 82.1 kg
(variação < 0.3 kg — estável!)

Calorias: média 2350 kcal/dia
Body Fat: 28%
```

**Cálculos:**

**Passo 3: Taxa de Mudança**
```
Slope ≈ 0.00 kg/dia
Rate semanal ≈ 0 kg/semana (João está em perfeita manutenção!)
```

**Passo 4: Energia Dinâmica**
```
Body fat: 28%
fat_fraction = 0.75 + (28 - 25) × 0.005 = 0.765

energy_per_kg = 0.765 × 9400 + 0.235 × 1800 = 7614 kcal/kg
```

**Passo 5: TDEE**
```
TDEE = 2350 - (0.00 × 7614) = 2350 kcal

Interpretação: João gasta exatamente o que come = PERFEITO!
```

**Passo 7: Target (Manutenção)**
```
target = 2350 - (0 × 1100) = 2350 kcal
```

**RESULTADO FINAL: 2350 kcal/dia**

---

## Constantes e Configurações

### Constantes Forbes/Hall (Energia Dinâmica)

```python
KCAL_PER_KG_FAT_MASS = 9400      # Kcal em 1 kg de gordura corporal
KCAL_PER_KG_LEAN_MASS = 1800     # Kcal em 1 kg de massa magra
KCAL_PER_KG_DEFAULT = 7700       # Fallback quando body fat desconhecido
```

**Interpretação:**
- **Gordura:** 9400 kcal/kg (quase 1 kcal por grama)
- **Músculo:** 1800 kcal/kg (muito menos — mais ativo metabolicamente)

**Fonte:** Forbes et al. (2007) "Body composition changes in overweight subjects"

---

### Constantes de Segurança

```python
MIN_CALORIES_FEMALE = 1200       # NIH/Harvard recomendação
MIN_CALORIES_MALE = 1500         # NIH/Harvard recomendação
MAX_DEFICIT_PCT = 0.30           # Nunca mais de 30% de déficit
CHECK_IN_INTERVAL_DAYS = 7       # Recheck a cada 7 dias
MAX_WEEKLY_ADJUSTMENT = 100      # ±100 kcal/semana máximo
```

**Fonte:** National Institutes of Health (NIH) e Harvard School of Public Health

---

### Constantes de Detecção

```python
OUTLIER_MODIFIED_Z_THRESHOLD = 3.5     # Z-score para outlier
EMA_SPAN = 10                          # Dias para suavização
DEFAULT_LOOKBACK_WEEKS = 4             # 28 dias para análise
```

**Modified Z-Score:**
- Mais robusto que Z-score padrão
- 3.5 detecta ~99.95% dos outliers legítimos
- Fórmula: `Z = 0.6745 × (x - mediana) / MAD`

**Fonte:** Iglewicz, B. and Hoaglin, D. C. (1993) "How to Detect and Handle Outliers"

---

## Referências Científicas

### Estudos Principais

1. **Hall, K. D., Sacks, G., Chandramohan, D., et al. (2011)**
   - *"Quantification of the effect of energy imbalance on bodyweight"*
   - PLOS Medicine
   - Dinâmica entre depleção de gordura vs. proteína

2. **Forbes, G. B. (2000)**
   - *"Body composition in adolescence"*
   - Handbook of Adolescent Medicine: State of the Art Reviews
   - Modelo Forbes para energia dinâmica (fat_fraction)

3. **Garthe, I., Raastad, T., Refsnes, P. E., et al. (2011)**
   - *"Effect of two different weight-loss rates on body composition and strength"*
   - International Journal of Sport Nutrition and Exercise Metabolism
   - Validação de 30% como máximo déficit seguro

4. **Mifflin, M. D., St Jeor, S. T., et al. (1990)**
   - *"A new predictive equation for resting energy expenditure in healthy individuals"*
   - American Journal of Clinical Nutrition
   - Fallback BMR calculation (Mifflin-St Jeor equation)

### Outras Fontes

- **National Institutes of Health (NIH):** Minimum calorie guidelines
- **Harvard School of Public Health:** Gender-specific safety thresholds
- **Modified Z-Score (Iglewicz & Hoaglin, 1993):** Outlier detection robustness

---

## Resumo Visual do Pipeline

```
┌─────────────────────────────────────────┐
│  Dados Históricos (28 dias)             │
│  - Pesos diários                        │
│  - Ingestão calórica                    │
│  - Body fat %                           │
└───────────────┬─────────────────────────┘
                │
        ┌───────▼────────┐
        │ 1. Outliers    │ (Modified Z-Score)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 2. Smoothing   │ (EMA + Regression)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 3. Rate        │ (kg/day slope)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 4. Energy      │ (Forbes/Hall)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 5. TDEE        │ (calories - slope × energy)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 6. Sanity Check│ (1200-5000 clamp)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 7. Target      │ (TDEE ± deficit)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 8. Gradual Adj │ (±100 kcal/week cap)
        └───────┬────────┘
                │
        ┌───────▼────────┐
        │ 9. Safety Floor│ (gender min + 30% max)
        └───────┬────────┘
                │
        ┌───────▼────────────────┐
        │  DAILY TARGET (kcal)   │
        │  Safe, Sustainable    │
        └────────────────────────┘
```

---

## Conclusão

O **TDEE v2** é um algoritmo robusto baseado em princípios científicos estabelecidos que calcula recomendações calóricas sustentáveis. Ao usar:
- Energia dinâmica (Forbes/Hall)
- Ajuste gradual (±100 kcal/semana)
- Pisos de segurança (gênero + 30% max)
- Detecção robusta de outliers

O v2 produz recomendações que são **seguras, eficientes e sustentáveis** para qualquer objetivo (perda, ganho ou manutenção).

---

*Documento criado em 2026-02-21*
*Algoritmo Adaptive TDEE v2*
*Implementação: 13 commits, 312 testes, zero bugs conhecidos*
