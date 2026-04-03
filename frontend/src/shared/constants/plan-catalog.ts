export type PlanId = 'free' | 'basic' | 'pro';

export interface PlanCatalogEntry {
  id: PlanId;
  highlight?: boolean;
  badgeKey?: string;
}

export const PLAN_CATALOG: PlanCatalogEntry[] = [
  { id: 'free' },
  { id: 'basic' },
  { id: 'pro', highlight: true, badgeKey: 'landing.plans.recommended' },
];

export interface PlanCardModel {
  id: PlanId;
  name: string;
  subtitle: string;
  priceLabel: string;
  features: string[];
  buttonLabel: string;
  highlight?: boolean;
  badge?: string;
}

export function getPlanPriceLabel(planId: PlanId, isPt: boolean): string {
  if (planId === 'free') {
    return isPt ? 'Grátis' : 'Free';
  }
  if (planId === 'basic') {
    return isPt ? 'R$ 24,90/mês' : '$4.99/mo';
  }
  return isPt ? 'R$ 49,90/mês' : '$9.99/mo';
}

export function buildPlanCardModel(
  entry: PlanCatalogEntry,
  t: (key: string, options?: Record<string, unknown>) => unknown,
  isPt: boolean
): PlanCardModel {
  const planKey = `landing.plans.items.${entry.id}`;
  return {
    id: entry.id,
    name: String(t(`${planKey}.name`)),
    subtitle: String(t(`${planKey}.description`)),
    priceLabel: getPlanPriceLabel(entry.id, isPt),
    features: t(`${planKey}.features`, { returnObjects: true }) as string[],
    buttonLabel: String(t(`${planKey}.button`)),
    highlight: entry.highlight,
    badge: entry.badgeKey ? String(t(entry.badgeKey)) : undefined,
  };
}
