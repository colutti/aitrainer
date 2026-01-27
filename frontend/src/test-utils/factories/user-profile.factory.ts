export interface UserProfile {
  id?: string;
  email: string;
  gender: 'Masculino' | 'Feminino';
  age: number;
  weight: number;
  height: number;
  goal: 'Ganhar massa' | 'Perder peso' | 'Manter' | 'Ganho de força';
  created_at?: string;
  updated_at?: string;
}

export class UserProfileFactory {
  static create(overrides?: Partial<UserProfile>): UserProfile {
    return {
      id: 'user_' + Date.now(),
      email: 'test@example.com',
      gender: 'Masculino',
      age: 30,
      weight: 80,
      height: 180,
      goal: 'Ganhar massa',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ...overrides
    };
  }

  static createMale(overrides?: Partial<UserProfile>): UserProfile {
    return this.create({
      gender: 'Masculino',
      weight: 85,
      height: 180,
      ...overrides
    });
  }

  static createFemale(overrides?: Partial<UserProfile>): UserProfile {
    return this.create({
      gender: 'Feminino',
      email: 'female@example.com',
      weight: 65,
      height: 165,
      ...overrides
    });
  }

  static createWeightLossGoal(overrides?: Partial<UserProfile>): UserProfile {
    return this.create({
      goal: 'Perder peso',
      weight: 95,
      ...overrides
    });
  }

  static createBulkGoal(overrides?: Partial<UserProfile>): UserProfile {
    return this.create({
      goal: 'Ganhar massa',
      weight: 75,
      ...overrides
    });
  }
}
