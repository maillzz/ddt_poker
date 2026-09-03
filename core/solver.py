from . import VERSION


def run(params: dict) -> dict:
    simulations = params.get("simulations", 10_000)

    return {
        "win_probability": 0.0,
        "tie_probability": 0.0,
        "loss_probability": 0.0,
        "ev": 0.0,
        "recommendation": "CALL",
        "simulations": simulations,
        "core_version": VERSION,
    }