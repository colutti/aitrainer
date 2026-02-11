"""
Pagination utilities.
"""

def calculate_total_pages(total: int, page_size: int) -> int:
    """Calculates total pages for pagination."""
    return (total + page_size - 1) // page_size if total > 0 else 0
