import { z } from 'zod';

export const userProfileSchema = z.object({
  display_name: z.string().min(2, 'O nome deve ter pelo menos 2 caracteres'),
  gender: z.string(),
  age: z.number().min(13, 'Idade mínima é 13 anos'),
  height: z.number().min(50, 'Altura inválida'),
  goal_type: z.enum(['lose', 'gain', 'maintain']),
  weekly_rate: z.number().min(0).max(2),
  target_weight: z.preprocess(
    (value) => {
      if (value === null || value === '' || value === undefined) return undefined;
      if (typeof value === 'number' && Number.isNaN(value)) return undefined;
      return value;
    },
    z.number().optional()
  ),
});

export type UserProfileForm = z.infer<typeof userProfileSchema>;
