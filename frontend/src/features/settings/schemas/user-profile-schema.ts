import { z } from 'zod';

export const userProfileSchema = z.object({
  display_name: z.string().min(2, 'O nome deve ter pelo menos 2 caracteres'),
  gender: z.string(),
  age: z.number().min(13, 'Idade mínima é 13 anos'),
  height: z.number().min(50, 'Altura inválida'),
});

export type UserProfileForm = z.infer<typeof userProfileSchema>;
