# Guia de Formatação de Datas e Números

## Visão Geral

Este documento descreve os padrões para formatação de datas e números em todo o frontend da aplicação. O aplicativo usa locale pt-BR (Português Brasileiro) em todos os formatos de data e número.

**Última atualização:** 27 de janeiro de 2026

---

## Datas

### Formato Padrão

Todas as datas devem exibir no formato **dd/MM/yyyy** ou variações conforme o caso de uso:

- **Display simples:** `27/01/2026`
- **Com mês alfabético:** `27 Jan 2026`
- **Com hora:** `27 Jan 2026 • 14:30`
- **Range de datas:** `01/01 a 31/01`

### Input de Data

Use o componente reutilizável `<app-date-input>`:

```html
<app-date-input
  label="Data de Nascimento"
  [ngModel]="dateValue()"
  (ngModelChange)="dateValue.set($event)"
  [required]="true">
</app-date-input>
```

**Props disponíveis:**
- `label` (string) - Rótulo exibido acima do input
- `placeholder` (string) - Placeholder padrão é "dd/mm/aaaa"
- `required` (boolean) - Marca campo como obrigatório
- `disabled` (boolean) - Desabilita o input
- `minDate` (NgbDateStruct) - Data mínima permitida
- `maxDate` (NgbDateStruct) - Data máxima permitida
- `[(ngModel)]` - Vinculação bidirecional (formato ISO YYYY-MM-DD)

**Exemplo completo:**
```html
<app-date-input
  label="Data do Treino"
  [ngModel]="workoutDate()"
  (ngModelChange)="workoutDate.set($event)"
  [minDate]="{year: 2024, month: 1, day: 1}"
  [maxDate]="{year: 2026, month: 12, day: 31}"
  [required]="true">
</app-date-input>
```

### Display de Data (Pipes)

Use o pipe customizado `appDateFormat` com formatos pré-definidos:

```html
<!-- Variações de formato -->
{{ date | appDateFormat:'medium' }}      <!-- 27/01/2026 -->
{{ date | appDateFormat:'short' }}       <!-- 27/01/26 -->
{{ date | appDateFormat:'long' }}        <!-- 27 Jan 2026 -->
{{ date | appDateFormat:'time' }}        <!-- 14:30 -->
{{ date | appDateFormat:'datetime' }}    <!-- 27 Jan 2026 • 14:30 -->
{{ date | appDateFormat:'dayMonth' }}    <!-- 27/01 -->
{{ date | appDateFormat:'shortMonth' }}  <!-- 27 Jan -->
{{ date | appDateFormat:'full' }}        <!-- 27/01/2026 14:30 -->
```

**Formatos disponíveis:**

| Formato | Padrão | Exemplo |
|---------|--------|---------|
| `short` | dd/MM/yy | 27/01/26 |
| `medium` (padrão) | dd/MM/yyyy | 27/01/2026 |
| `long` | dd MMM yyyy | 27 Jan 2026 |
| `time` | HH:mm | 14:30 |
| `datetime` | dd MMM yyyy • HH:mm | 27 Jan 2026 • 14:30 |
| `shortMonth` | dd MMM | 27 Jan |
| `dayMonth` | dd/MM | 27/01 |
| `full` | dd/MM/yyyy HH:mm | 27/01/2026 14:30 |

**Casos de uso comuns:**
```html
<!-- Header de data/hora -->
{{ event.date | appDateFormat:'datetime' }}

<!-- Range de datas -->
{{ startDate | appDateFormat:'dayMonth' }} a {{ endDate | appDateFormat:'dayMonth' }}

<!-- Data em tabela (compacta) -->
{{ log.date | appDateFormat:'short' }}

<!-- Hora apenas -->
{{ event.date | appDateFormat:'time' }}
```

**Como adicionar o pipe a um componente:**
```typescript
import { AppDateFormatPipe } from '@pipes/date-format.pipe';

@Component({
  selector: 'app-my-component',
  imports: [CommonModule, AppDateFormatPipe],
  template: `{{ date | appDateFormat:'medium' }}`
})
export class MyComponent {}
```

---

## Números

### Formato Padrão

Números decimais exibem com **ponto (.)** como separador, conforme padrão pt-BR:

- **Inteiros:** `72` (sem decimais)
- **Uma casa:** `72.5`
- **Duas casas:** `72.45`
- **Números grandes:** `1.500.5` (ponto para milhares, ponto para decimal)

### Input Numérico

Use o componente reutilizável `<app-number-input>`:

```html
<app-number-input
  label="Peso"
  unit="kg"
  [ngModel]="weight()"
  (ngModelChange)="weight.set($event)"
  [min]="30"
  [max]="500"
  [step]="0.1">
</app-number-input>
```

**Props disponíveis:**
- `label` (string) - Rótulo exibido acima do input
- `placeholder` (string) - Placeholder padrão é "0.0"
- `unit` (string) - Unidade exibida ao lado (kg, %, cm, etc)
- `min` (number) - Valor mínimo
- `max` (number) - Valor máximo
- `step` (number) - Incremento ao usar setas (padrão 0.1)
- `required` (boolean) - Marca campo como obrigatório
- `disabled` (boolean) - Desabilita o input
- `[(ngModel)]` - Vinculação bidirecional

**Exemplo completo:**
```html
<app-number-input
  label="Percentual de Gordura"
  unit="%"
  [ngModel]="bodyFat()"
  (ngModelChange)="bodyFat.set($event)"
  [min]="0"
  [max]="100"
  [step]="0.1"
  [required]="true">
</app-number-input>
```

**Comportamento do Input:**
- ✅ Aceita ponto (`.`) como separador decimal
- ✅ Aceita vírgula (`,`) como separador decimal (converte automaticamente)
- ✅ Armazena internamente como número (. ou ,)
- ✅ Impede entrada de múltiplos separadores decimais
- ✅ Suporta navegação com setas do teclado (incremento/decremento por `step`)

### Display de Número (Pipes)

Use o pipe customizado `appNumberFormat` com formatos pré-definidos:

```html
<!-- Variações de formato -->
{{ value | appNumberFormat:'integer' }}    <!-- 72 (sem decimais) -->
{{ value | appNumberFormat:'decimal1' }}   <!-- 72.5 (1 casa decimal) -->
{{ value | appNumberFormat:'decimal2' }}   <!-- 72.45 (2 casas decimais) -->
{{ value | appNumberFormat:'weight' }}     <!-- 72.5 (alias para decimal1) -->
{{ value | appNumberFormat:'percentage' }} <!-- 72.45 (alias para decimal2) -->
```

**Formatos disponíveis:**

| Formato | Padrão | Casas Decimais | Uso |
|---------|--------|----------------|----|
| `integer` | 1.0-0 | 0 | TDEE, calorias totais |
| `decimal1` | 1.1-1 | 1 | Peso, variações, macros |
| `decimal2` | 1.2-2 | 2 | Percentuais, IMC, taxas |
| `weight` | 1.1-1 | 1 | Alias para peso |
| `percentage` | 1.2-2 | 2 | Alias para percentuais |

**Casos de uso comuns:**
```html
<!-- Peso com unidade -->
{{ weight | appNumberFormat:'weight' }} kg

<!-- Percentuais com símbolo -->
{{ bodyFat | appNumberFormat:'percentage' }}%

<!-- TDEE (sem decimais) -->
{{ tdee | appNumberFormat:'integer' }} kcal/dia

<!-- Variação de peso -->
{{ getWeightChange() > 0 ? '+' : '' }}{{ getWeightChange() | appNumberFormat:'weight' }} kg

<!-- Tabela com valores variados -->
<td>{{ calories | appNumberFormat:'integer' }}</td>
<td>{{ protein | appNumberFormat:'decimal1' }}g</td>
<td>{{ variation | appNumberFormat:'decimal2' }}%</td>
```

**Como adicionar o pipe a um componente:**
```typescript
import { AppNumberFormatPipe } from '@pipes/number-format.pipe';

@Component({
  selector: 'app-my-component',
  imports: [CommonModule, AppNumberFormatPipe],
  template: `{{ value | appNumberFormat:'weight' }} kg`
})
export class MyComponent {}
```

---

## Regras Gerais

### ✅ Faça:
1. **Sempre use os pipes customizados** para datas e números no template
2. **Sempre use os componentes compartilhados** para novos inputs de data/número
3. **Use formato ISO (YYYY-MM-DD)** internamente (no TypeScript/API)
4. **Deixe o componente fazer a conversão** entre ISO e display
5. **Reutilize os componentes** em vez de criar inputs customizados

### ❌ Não faça:
1. ❌ Não use `| date` ou `| number` pipes diretamente
2. ❌ Não crie inputs de data/número sem usar os componentes compartilhados
3. ❌ Não misture formatos de data na mesma interface
4. ❌ Não tente formatar datas manualmente com `toLocaleDateString()`
5. ❌ Não use múltiplos separadores decimais (sempre . internamente)

---

## Integração com TypeScript

### Armazenar Datas

Sempre armazene datas em formato ISO internamente:

```typescript
// ✅ Correto
entryDate = signal<string>(new Date().toISOString().split('T')[0]); // YYYY-MM-DD
workoutDate = signal<string>('2026-01-27'); // ISO

// ❌ Errado
dateFormatted = signal<string>('27/01/2026'); // Não use formato formatado internamente
dateObject = signal<Date>(new Date()); // Evite armazenar Date objects em signals
```

### Armazenar Números

Sempre armazene números como número, não como string:

```typescript
// ✅ Correto
weight = signal<number>(72.5);
bodyFat = signal<number | null>(18.45);

// ❌ Errado
weightStr = signal<string>('72.5'); // Não use string
weightFormatted = signal<string>('72,5'); // Não use formatado
```

### Exemplo Completo

```typescript
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DateInputComponent } from '@components/shared/date-input/date-input.component';
import { NumberInputComponent } from '@components/shared/number-input/number-input.component';
import { AppDateFormatPipe } from '@pipes/date-format.pipe';
import { AppNumberFormatPipe } from '@pipes/number-format.pipe';

@Component({
  selector: 'app-weight-log',
  imports: [
    CommonModule,
    DateInputComponent,
    NumberInputComponent,
    AppDateFormatPipe,
    AppNumberFormatPipe
  ],
  template: `
    <form>
      <!-- Input de data -->
      <app-date-input
        label="Data"
        [ngModel]="logDate()"
        (ngModelChange)="logDate.set($event)"
        [required]="true">
      </app-date-input>

      <!-- Input de número -->
      <app-number-input
        label="Peso"
        unit="kg"
        [ngModel]="logWeight()"
        (ngModelChange)="logWeight.set($event)"
        [min]="30"
        [max]="500"
        [step]="0.1"
        [required]="true">
      </app-number-input>

      <!-- Display formatado -->
      <p>Última medição: {{ logDate() | appDateFormat:'medium' }}</p>
      <p>Peso: {{ logWeight() | appNumberFormat:'weight' }} kg</p>
    </form>
  `
})
export class WeightLogComponent {
  // Armazenar em formato padrão
  logDate = signal<string>(new Date().toISOString().split('T')[0]); // YYYY-MM-DD
  logWeight = signal<number>(72.5);
}
```

---

## Resolução de Problemas

### Problema: Pipe não funciona no template
**Solução:** Adicione o pipe aos imports do componente:
```typescript
imports: [CommonModule, AppDateFormatPipe, AppNumberFormatPipe]
```

### Problema: Componente de input não está formatando
**Solução:** Certifique-se de que está usando a vinculação correta:
```html
<!-- ✅ Correto -->
[ngModel]="value()"
(ngModelChange)="value.set($event)"

<!-- ❌ Errado -->
[value]="value()"  <!-- Não funciona com componente -->
```

### Problema: Input numérico não aceita vírgula
**Solução:** Verifique se `appNumericInput` está adicionado. Se usar `<app-number-input>`, a diretiva já está embutida.

### Problema: Data não exibe no formato esperado
**Solução:** Verifique o formato do pipe:
```html
<!-- Usar alias correto -->
{{ date | appDateFormat:'medium' }}

<!-- Não use formatos do Angular -->
{{ date | date:'dd/MM/yyyy' }} <!-- ❌ Errado -->
```

---

## Migrando Código Antigo

Se encontrar código usando pipes antigos, migre assim:

### Datas
```typescript
// Antes
{{ date | date:'dd/MM/yyyy' }}
{{ date | date:'HH:mm' }}

// Depois
{{ date | appDateFormat:'medium' }}
{{ date | appDateFormat:'time' }}
```

### Números
```typescript
// Antes
{{ value | number:'1.0-0' }}
{{ value | number:'1.1-1' }}
{{ value | number:'1.2-2' }}

// Depois
{{ value | appNumberFormat:'integer' }}
{{ value | appNumberFormat:'weight' }}
{{ value | appNumberFormat:'percentage' }}
```

### Inputs
```html
<!-- Antes -->
<input type="date" [ngModel]="date()" (ngModelChange)="date.set($event)">
<input type="number" [ngModel]="weight()" (ngModelChange)="weight.set($event)">

<!-- Depois -->
<app-date-input [ngModel]="date()" (ngModelChange)="date.set($event)"></app-date-input>
<app-number-input [ngModel]="weight()" (ngModelChange)="weight.set($event)" unit="kg"></app-number-input>
```

---

## Referência de Componentes

### DateInputComponent
**Localização:** `src/components/shared/date-input/date-input.component.ts`
**Funcionalidade:** Input de data com ng-bootstrap datepicker
**Emite:** String ISO (YYYY-MM-DD)

### NumberInputComponent
**Localização:** `src/components/shared/number-input/number-input.component.ts`
**Funcionalidade:** Input numérico com diretiva appNumericInput
**Suporta:** Vírgula e ponto como decimal

### AppDateFormatPipe
**Localização:** `src/pipes/date-format.pipe.ts`
**Funcionalidade:** Formatação de datas em 8 variações
**Locale:** pt-BR

### AppNumberFormatPipe
**Localização:** `src/pipes/number-format.pipe.ts`
**Funcionalidade:** Formatação de números em 5 variações
**Locale:** pt-BR

---

## Próximos Passos

Para adicionar suporte a outros locales no futuro:
1. Registre a locale no `main.ts`
2. Atualize os testes dos pipes
3. Teste com dados reais da locale
4. Atualize este documento

Para adicionar novos formatos de data/número:
1. Adicione a entrada aos `formats` maps nos pipes
2. Atualize este documento
3. Adicione testes
4. Revise a alteração
