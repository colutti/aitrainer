export interface TrainerProfile {
  trainer_type: string;
}

export interface TrainerOption {
  trainer_id: string;
  name: string;
  avatar_url: string;
  description?: string;
}

export class TrainerFactory {
  static create(type: string = 'atlas'): TrainerProfile {
    return {
      trainer_type: type
    };
  }

  static createOption(
    id: string = 'atlas',
    name: string = 'Atlas',
    overrides?: Partial<TrainerOption>
  ): TrainerOption {
    return {
      trainer_id: id,
      name: name,
      avatar_url: `/assets/${id}.png`,
      description: `${name} trainer personality`,
      ...overrides
    };
  }

  static createAllTrainers(): TrainerOption[] {
    const trainers = [
      { id: 'atlas', name: 'Atlas' },
      { id: 'luna', name: 'Luna' },
      { id: 'sofia', name: 'Sofia' },
      { id: 'sargento', name: 'Sargento' },
      { id: 'gymbro', name: 'GymBro' }
    ];

    return trainers.map(t => this.createOption(t.id, t.name));
  }

  static createAtlas(): TrainerOption {
    return this.createOption('atlas', 'Atlas', {
      description: 'Strong and disciplined trainer'
    });
  }

  static createLuna(): TrainerOption {
    return this.createOption('luna', 'Luna', {
      description: 'Balanced and thoughtful trainer'
    });
  }

  static createSofia(): TrainerOption {
    return this.createOption('sofia', 'Sofia', {
      description: 'Motivating and energetic trainer'
    });
  }
}
