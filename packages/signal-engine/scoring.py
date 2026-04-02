def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def normalize(value: float, floor: float, ceiling: float) -> float:
    if ceiling <= floor:
        return 0.0
    return clamp((value - floor) / (ceiling - floor))


def calculate_score(
    components: dict[str, float], weights: dict[str, float] | None = None
) -> float:
    if not components:
        return 1.0

    resolved_weights = weights or {key: 1.0 for key in components}
    total_weight = sum(resolved_weights.get(key, 1.0) for key in components)

    if total_weight == 0:
        return 1.0

    weighted_score = sum(
        clamp(components[key]) * resolved_weights.get(key, 1.0)
        for key in components
    ) / total_weight

    return round(1.0 + (weighted_score * 9.0), 1)


def score_to_confidence(score: float, evidence_count: int = 0) -> float:
    evidence_bonus = min(evidence_count, 4) * 3.0
    base_confidence = (score * 8.5) + evidence_bonus
    return round(clamp(base_confidence, 35.0, 98.0), 1)

