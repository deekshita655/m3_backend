def classify(
    ph: float = None,
    tds: float = None,
    nh3: float = None,
    tds_stable: float = None,
    nh3_slope: float = None
):
    """
    Provisional milk classification logic.

    Missing measurements are not treated as zero.
    Classification is withheld when required inputs are unavailable.
    """

    # Do not make a classification using incomplete hardware data.
    if tds is None or nh3 is None:
        return {
            "status": "UNCLASSIFIED",
            "reason": (
                "Insufficient sensor data for classification. "
                "TDS and calibrated NH3 measurements are required."
            ),
            "confidence": 0.0
        }

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
            "reason": "Excessive TDS detected (Salt adulteration)",
            "confidence": 0.95
        }

    # 3. Check for Water Dilution
    if tds < 650.0:
        return {
            "status": "ADULTERATED",
            "reason": "Low TDS detected (Water dilution)",
            "confidence": 0.92
        }

    # 4. Check for Sugar Adulteration
    if 1200.0 <= tds <= 1800.0:
        return {
            "status": "ADULTERATED",
            "reason": "Elevated TDS range detected (Sugar adulteration)",
            "confidence": 0.88
        }

    # 5. Check for Urea Adulteration
    if (
        ph is not None
        and ph > 7.0
        and nh3_slope is not None
        and nh3_slope > 0.5
    ):
        return {
            "status": "ADULTERATED",
            "reason": "High pH combined with positive NH3 slope detected (Urea adulteration)",
            "confidence": 0.94
        }

    # 6. Check for Starch Adulteration
    if tds_stable is not None and tds_stable > 10.0:
        return {
            "status": "ADULTERATED",
            "reason": "Delayed TDS stabilization detected (possible starch adulteration)",
            "confidence": 0.90
        }

    # 7. Baseline classification
    return {
        "status": "PURE",
        "reason": "All available measurements fall within provisional baseline parameters",
        "confidence": 0.99
    }