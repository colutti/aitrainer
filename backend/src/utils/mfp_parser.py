"""
Parser for MyFitnessPal text-based logs.
"""

import re
from datetime import date
from typing import List, Dict, Any

MONTHS_PT = {
    "jan": 1,
    "fev": 2,
    "mar": 3,
    "abr": 4,
    "mai": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "set": 9,
    "out": 10,
    "nov": 11,
    "dez": 12,
}


def parse_mfp_text(text: str) -> List[Dict[str, Any]]:
    """
    Parses a text block copied from MyFitnessPal website.
    Detects dates like '19 de mar. de 2026' and 'TOTAIS' lines.
    """
    results = []

    # Split text into potential day blocks.
    # Pattern: 'D de MMM. de YYYY' or 'D de MMMM de YYYY'
    date_pattern = re.compile(
        r"(\d{1,2})\s+de\s+(\w+)\.?\s+de\s+(\d{4})", re.IGNORECASE
    )

    # Split the text by lines and look for data
    lines = text.strip().split("\n")

    current_date = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line is a date
        date_match = date_pattern.search(line)
        if date_match:
            day_num = int(date_match.group(1))
            month_str = date_match.group(2).lower()[:3]
            year_num = int(date_match.group(3))

            month_num = MONTHS_PT.get(month_str)
            if month_num:
                current_date = date(year_num, month_num, day_num)
                continue

        # Check if line is a TOTAIS line
        if "TOTAIS" in line.upper() and current_date:
            # MFP column order in web view usually is:
            # Calories, Carbs, Fat, Protein, Cholest, Sodium, Sugar, Fiber

            # Remove "TOTAIS" and units
            cleaned_line = (
                line.replace("TOTAIS", "").replace("g", "").replace("mg", "").strip()
            )
            # Find all numbers (including floats)
            numbers = re.findall(r"[-+]?\d*\.?\d+", cleaned_line)

            if len(numbers) >= 4:
                day_data = {
                    "date": current_date,
                    "calories": int(round(float(numbers[0]))),
                    "carbs": float(numbers[1]),
                    "fat": float(numbers[2]),
                    "protein": float(numbers[3]),
                }

                # Optional fields
                if len(numbers) >= 5:
                    day_data["cholesterol"] = float(numbers[4])
                if len(numbers) >= 6:
                    day_data["sodium"] = float(numbers[5])
                if len(numbers) >= 7:
                    day_data["sugar"] = float(numbers[6])
                if len(numbers) >= 8:
                    day_data["fiber"] = float(numbers[7])

                results.append(day_data)
                current_date = None  # Reset for next date

    return results
