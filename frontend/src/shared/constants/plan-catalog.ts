export type PlanId = 'free' | 'pro';

export interface PlanCatalogEntry {
  id: PlanId;
  highlight?: boolean;
  badgeKey?: string;
}

export const PLAN_CATALOG: PlanCatalogEntry[] = [
  { id: 'free' },
  { id: 'pro', highlight: true, badgeKey: 'landing.plans.recommended' },
];

export interface PlanCardModel {
  id: PlanId;
  name: string;
  subtitle: string;
  priceLabel: string;
  fullPriceLabel?: string;
  features: string[];
  buttonLabel: string;
  highlight?: boolean;
  badge?: string;
}

export function getPlanPriceLabel(planId: PlanId, isPt: boolean): string {
  if (planId === 'free') {
    return isPt ? 'Grátis' : 'Free';
  }
  return isPt ? 'R$ 4,99/mês' : '$4.99/mo';
}

export function getPlanFullPriceLabel(planId: PlanId, isPt: boolean): string | undefined {
  if (planId !== 'pro') {
    return undefined;
  }
  return isPt ? 'R$ 6,99/mês' : '$6.99/mo';
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
    fullPriceLabel: getPlanFullPriceLabel(entry.id, isPt),
    features: t(`${planKey}.features`, { returnObjects: true }) as string[],
    buttonLabel: String(t(`${planKey}.button`)),
    highlight: entry.highlight,
    badge: entry.badgeKey ? String(t(entry.badgeKey)) : undefined,
  };
}
