PLAN_FREE = "free"
PLAN_PRO = "pro"
PLAN_PRO_PLUS = "pro_plus"

PLAN_SIGNAL_LIMITS: dict[str, int | None] = {
    PLAN_FREE: 2,
    PLAN_PRO: None,
    PLAN_PRO_PLUS: None,
}

CHECKOUT_ENABLED_PLANS = {PLAN_PRO, PLAN_PRO_PLUS}


def normalize_plan(plan: str | None) -> str:
    if not plan:
        return PLAN_FREE

    normalized = plan.strip().lower()
    if normalized in {"starter", "free"}:
        return PLAN_FREE
    if normalized in {"pro", "professional"}:
        return PLAN_PRO
    if normalized in {"pro+", "pro_plus", "pro-plus", "desk"}:
        return PLAN_PRO_PLUS
    return PLAN_FREE


def get_signal_limit(plan: str | None) -> int | None:
    return PLAN_SIGNAL_LIMITS.get(normalize_plan(plan), PLAN_SIGNAL_LIMITS[PLAN_FREE])


def can_access_all_signals(plan: str | None) -> bool:
    return get_signal_limit(plan) is None


def can_checkout(plan: str | None) -> bool:
    return normalize_plan(plan) in CHECKOUT_ENABLED_PLANS
