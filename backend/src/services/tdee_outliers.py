"""
Utility functions for filtering outliers in weight logs for Adaptive TDEE.
"""

from typing import List
import numpy as np

from src.core.logs import logger
from src.api.models.weight_log import WeightLog

# Outlier detection configuration
OUTLIER_MODIFIED_Z_THRESHOLD = 3.5
MAX_DAILY_WEIGHT_CHANGE = 1.0  # kg



def pass1_statistical_filter(
    sorted_logs: List[WeightLog],
) -> tuple[List[WeightLog], int]:
    """Applies Modified Z-Score filter to remove anomalous weight readings."""
    weights = np.array([log.weight_kg for log in sorted_logs])
    median = np.median(weights)
    mad = np.median(np.abs(weights - median))

    if mad == 0:
        return list(sorted_logs), 0

    statistical_clean = []
    stat_removed = 0
    modified_z_scores = 0.6745 * (weights - median) / mad
    for i, log in enumerate(sorted_logs):
        if abs(modified_z_scores[i]) > OUTLIER_MODIFIED_Z_THRESHOLD:
            logger.info(
                "Modified Z-Score outlier: %.1f kg on %s (z=%.2f)",
                log.weight_kg, log.date, modified_z_scores[i],
            )
            stat_removed += 1
        else:
            statistical_clean.append(log)
    return statistical_clean, stat_removed


def pass2_contextual_filter(
    statistical_clean: List[WeightLog],
) -> tuple[List[WeightLog], int]:
    """Applies contextual filtering to handle steps and transient spikes."""
    clean_logs = [statistical_clean[0]]
    last_valid_log = statistical_clean[0]
    contextual_removed = 0

    i = 1
    while i < len(statistical_clean):
        curr = statistical_clean[i]
        delta = abs(curr.weight_kg - last_valid_log.weight_kg)
        days_diff = (curr.date - last_valid_log.date).days

        if delta > MAX_DAILY_WEIGHT_CHANGE and days_diff <= 3:
            if i + 1 < len(statistical_clean):
                next_log = statistical_clean[i + 1]
                dist_to_baseline = abs(
                    next_log.weight_kg - last_valid_log.weight_kg
                )

                if dist_to_baseline < delta:
                    logger.info(
                        "Ignoring transient weight spike: %s kg on %s",
                        curr.weight_kg, curr.date,
                    )
                    contextual_removed += 1
                    i += 1
                    continue

                logger.info(
                    "Detected Step Change: %s -> %s. Resetting baseline.",
                    last_valid_log.weight_kg, curr.weight_kg,
                )
                contextual_removed += len(clean_logs)
                clean_logs = [curr]
                last_valid_log = curr
                i += 1
                continue

            logger.info(
                "Last weight log shows large jump: %s -> %s",
                last_valid_log.weight_kg, curr.weight_kg,
            )

        clean_logs.append(curr)
        last_valid_log = curr
        i += 1

    return clean_logs, contextual_removed


def filter_outliers(logs: List[WeightLog]) -> tuple[List[WeightLog], int]:
    """
    Filters out weight anomalies using a two-pass approach:
    1. Modified Z-Score (statistical) — catches extreme one-off values
    2. Contextual (semantic) — handles step changes and transient spikes

    Returns:
        tuple: (filtered_logs, count_of_removed_logs)
    """
    if len(logs) < 3:
        return logs, 0

    sorted_logs = sorted(logs, key=lambda x: x.date)

    statistical_clean, stat_removed = pass1_statistical_filter(sorted_logs)

    if len(statistical_clean) < 3:
        return statistical_clean, stat_removed

    clean_logs, contextual_removed = pass2_contextual_filter(
        statistical_clean
    )

    return clean_logs, stat_removed + contextual_removed
