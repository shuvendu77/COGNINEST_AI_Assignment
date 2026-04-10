import math


def sanitize_value(v):
    """Replace nan/inf float values with None for JSON compliance."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v
