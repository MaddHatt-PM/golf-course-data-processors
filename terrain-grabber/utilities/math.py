def clamp01(value) -> float:
    return max(min(value, 1.0), 0.0)

def clamp(value, min_value, max_value) -> float:
    return max(min(value, max_value), min_value)

def meter_to_feet(m:float) -> float:
    return m / 0.3048

def feet_to_meter(f:float) -> float:
    return f * 0.3048