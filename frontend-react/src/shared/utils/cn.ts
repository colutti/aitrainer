import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for merging tailwind classes safely using clsx and tailwind-merge.
 * Ensures that tailwind classes are merged correctly and conflicts are resolved.
 * 
 * @param inputs - Array of class values to merge
 * @returns A string of merged class names
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
