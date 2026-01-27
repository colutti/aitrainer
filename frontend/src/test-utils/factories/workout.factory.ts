export interface Workout {
  id: string;
  date: string;
  type: string;
  exercises: Exercise[];
  duration_minutes: number;
  notes?: string;
}

export interface Exercise {
  name: string;
  sets: number;
  reps: number;
  weight?: number;
}

export class WorkoutFactory {
  static create(overrides?: Partial<Workout>): Workout {
    return {
      id: 'workout_' + Date.now(),
      date: new Date().toISOString().split('T')[0],
      type: 'Peito',
      exercises: [
        { name: 'Supino Reto', sets: 4, reps: 8, weight: 100 },
        { name: 'Crucifixo', sets: 3, reps: 10, weight: 20 }
      ],
      duration_minutes: 45,
      ...overrides
    };
  }

  static createList(count: number, type?: string): Workout[] {
    const types = ['Peito', 'Costas', 'Pernas', 'Ombro', 'Braço'];
    return Array.from({ length: count }, (_, i) => {
      const baseDate = new Date();
      baseDate.setDate(baseDate.getDate() - i);
      return this.create({
        id: `workout_${i}`,
        type: type || types[i % types.length],
        date: baseDate.toISOString().split('T')[0]
      });
    });
  }

  static createChest(): Workout {
    return this.create({
      type: 'Peito',
      exercises: [
        { name: 'Supino Reto', sets: 4, reps: 8, weight: 100 },
        { name: 'Supino Inclinado', sets: 4, reps: 10, weight: 80 },
        { name: 'Crucifixo', sets: 3, reps: 12, weight: 20 }
      ]
    });
  }

  static createBack(): Workout {
    return this.create({
      type: 'Costas',
      exercises: [
        { name: 'Barra Fixa', sets: 4, reps: 8 },
        { name: 'Remada com Barra', sets: 4, reps: 10, weight: 80 },
        { name: 'Remada Machine', sets: 3, reps: 12, weight: 120 }
      ]
    });
  }
}
