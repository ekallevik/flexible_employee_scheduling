def get_weights():
    return {
        "rest": 5,
        "contracted hours": 1,
        "partial weekends": 1,
        "isolated working days": 1,
        "isolated off days": 1,
        "consecutive days": 1,
        "backward rotation": 1,
        "preferences": 1,
        "lowest fairness score": 1,
        "demand_deviation": 5,
    }


def get_shift_design_weights():
    return {"demand_deviation": 5, "shift_duration": 15}
