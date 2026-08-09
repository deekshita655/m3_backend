# classifier.py (M1's Logic Module)

def classify(
    ph: float, 
    tds: float, 
    nh3: float, 
    tds_stable: float = None, 
    nh3_slope: float = None
):
    """
    Classifies milk samples based on threshold standards research (M1 Day 1 & Day 2).
    Returns a dictionary with status, reason, and confidence.
    """
    # 1. Check for Spoiled Milk
    if nh3 > 20.0:
        return {
            "status": "SPOILED",
            "reason": "Ammonia (NH3) level exceeds critical threshold (> 20.0)",
            "confidence": 0.98
        }
        
    # 2. Check for Salt Adulteration
    if tds > 2000.0:
        return {
            "status": "ADULTERATED",
            "reason": "Excessive Total Dissolved Solids detected (Salt adulteration: TDS > 2000)",
            "confidence": 0.95
        }
        
    # 3. Check for Water Dilution
    if tds < 650.0:
        return {
            "status": "ADULTERATED",
            "reason": "Low Total Dissolved Solids detected (Water dilution: TDS < 650)",
            "confidence": 0.92
        }

    # 4. Check for Sugar Adulteration
    if 1200.0 <= tds <= 1800.0:
        return {
            "status": "ADULTERATED",
            "reason": "Elevated TDS range detected (Sugar adulteration: TDS 1200-1800)",
            "confidence": 0.88
        }

    # 5. Check for Urea Adulteration
    if ph > 7.0 and (nh3_slope is not None and nh3_slope > 0.5):
        return {
            "status": "ADULTERATED",
            "reason": "High pH combined with positive NH3 slope detected (Urea adulteration)",
            "confidence": 0.94
        }

    # 6. Check for Starch Adulteration
    if tds_stable is not None and tds_stable > 10.0:
        return {
            "status": "ADULTERATED",
            "reason": "TDS stabilization time delayed (> 10s indicates Starch binder)",
            "confidence": 0.90
        }

    # 7. Baseline Pure Milk
    return {
        "status": "PURE",
        "reason": "All sensor values fall within baseline non-adulterated milk parameters",
        "confidence": 0.99
    }