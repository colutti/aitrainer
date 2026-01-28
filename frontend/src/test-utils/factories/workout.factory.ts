import { Workout, Exercise } from '../../models/workout.model';

export class WorkoutFactory {
  static create(overrides?: Partial<Workout>): Workout {
    return {
      id: 'workout_' + Date.now(),
      date: new Date().toISOString().split('T')[0],
      workout_type: 'Peito',
      exercises: [
        { name: 'Supino Reto', sets: 4, reps_per_set: [8, 8, 8, 8], weights_per_set: [100, 100, 100, 100] },
        { name: 'Crucifixo', sets: 3, reps_per_set: [10, 10, 10], weights_per_set: [20, 20, 20] }
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
        workout_type: type || types[i % types.length],
        date: baseDate.toISOString().split('T')[0]
      });
    });
  }

  static createChest(): Workout {
    return this.create({
      workout_type: 'Peito',
      exercises: [
        { name: 'Supino Reto', sets: 4, reps_per_set: [8, 8, 8, 8], weights_per_set: [100, 100, 100, 100] },
        { name: 'Supino Inclinado', sets: 4, reps_per_set: [10, 10, 10, 10], weights_per_set: [80, 80, 80, 80] },
        { name: 'Crucifixo', sets: 3, reps_per_set: [12, 12, 12], weights_per_set: [20, 20, 20] }
      ]
    });
  }

  static createBack(): Workout {
    return this.create({
      workout_type: 'Costas',
      exercises: [
        { name: 'Barra Fixa', sets: 4, reps_per_set: [8, 8, 8, 8], weights_per_set: [0, 0, 0, 0] },
        { name: 'Remada com Barra', sets: 4, reps_per_set: [10, 10, 10, 10], weights_per_set: [80, 80, 80, 80] },
        { name: 'Remada Machine', sets: 3, reps_per_set: [12, 12, 12], weights_per_set: [120, 120, 120] }
      ]
    });
  }
}
