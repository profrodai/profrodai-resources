"""Choose from deliberately fictional cost/latency fixtures."""
from __future__ import annotations
import json

def choose(models: list[dict[str, object]], max_latency: int) -> dict[str, object] | None:
    eligible = [model for model in models if int(model["latency_ms"]) <= max_latency]
    return min(eligible, key=lambda model: float(model["cost"])) if eligible else None

if __name__ == "__main__":
    models = [{"name":"fixture-fast", "latency_ms":120, "cost":0.8}, {"name":"fixture-value", "latency_ms":180, "cost":0.3}]
    print(json.dumps(choose(models, 200), sort_keys=True))
