from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from config import get_settings
from models.schemas import (
    ConfluenceSetupResponse,
    SetupSignalComponent,
    SignalActionPlan,
    SignalConfirmation,
    SignalDataQualityWarning,
    SignalKeyData,
    SignalProPlusFollowUp,
)
from services.plans import PLAN_FREE, PLAN_PRO_PLUS, normalize_plan
from services.pro_signal_view import (
    ACTION_DISCARD,
    ACTION_ENTER,
    ACTION_WAIT,
    EXECUTION_DISCARD,
    EXECUTION_EXECUTABLE,
    EXECUTION_WAIT_CONFIRMATION,
    EXECUTION_WATCHLIST,
    SEVERITY_NEGATIVE,
    SEVERITY_POSITIVE,
    SEVERITY_WARNING,
)


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coerce_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_confidence_pct(value: Any) -> float:
    numeric = _coerce_float(value, 0.0) or 0.0
    return round(numeric * 100.0, 1) if 0.0 <= numeric <= 1.0 else round(numeric, 1)


def _normalize_direction(value: Any) -> str:
    normalized = str(value or "neutral").strip().lower()
    if normalized not in {"bullish", "bearish", "neutral"}:
        return "neutral"
    return normalized


def _round_level(value: float | None) -> float | None:
    if value is None:
        return None

    absolute = abs(value)
    if absolute >= 1000:
        return round(value, 0)
    if absolute >= 100:
        return round(value, 1)
    if absolute >= 1:
        return round(value, 2)
    return round(value, 4)


def _extract_first_sentence(text: str, max_length: int = 170) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "Sin tesis disponible."

    for separator in (". ", ".\n", "\n"):
        sentence, _, _ = cleaned.partition(separator)
        if sentence:
            cleaned = sentence
            break

    cleaned = cleaned.rstrip(".")
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 1].rstrip()
    return f"{cleaned}."


def _build_key_data(snapshot: dict[str, Any] | None) -> SignalKeyData:
    source = str((snapshot or {}).get("source", "runtime"))
    return SignalKeyData(
        price=_coerce_float((snapshot or {}).get("price_usd"), None),
        change_24h=_coerce_float((snapshot or {}).get("change_24h"), None),
        volume_24h=_coerce_float((snapshot or {}).get("volume_24h"), None),
        funding=_coerce_float((snapshot or {}).get("funding_rate"), None),
        oi_change_24h=_coerce_float((snapshot or {}).get("oi_change_24h"), None),
        timeframe_base=str((snapshot or {}).get("timeframe", "1D")),
        source=source,
    )


def build_setup_data_quality_warnings(
    setup: dict[str, Any],
    snapshot: dict[str, Any] | None = None,
) -> list[SignalDataQualityWarning]:
    flags = _get_value(setup, "quality_flags", {}) or {}
    warnings: list[SignalDataQualityWarning] = []

    if flags.get("snapshot_missing"):
        warnings.append(
            SignalDataQualityWarning(
                code="snapshot_missing",
                severity=SEVERITY_NEGATIVE,
                message="No hay snapshot enlazado a este setup. La lectura operativa queda degradada.",
            )
        )
    if flags.get("mock_contamination"):
        warnings.append(
            SignalDataQualityWarning(
                code="mock_contamination",
                severity=SEVERITY_NEGATIVE,
                message="Parte del contexto usa fallback mock o defaults del MVP. No lo trates como setup fully validated.",
            )
        )
    if flags.get("liquidations_unverified"):
        warnings.append(
            SignalDataQualityWarning(
                code="liquidations_unverified",
                severity=SEVERITY_WARNING,
                message="La lectura de liquidaciones no viene de un feed dedicado completo en este entorno.",
            )
        )
    if flags.get("oi_inferred"):
        warnings.append(
            SignalDataQualityWarning(
                code="oi_inferred",
                severity=SEVERITY_WARNING,
                message="El open interest no llega completo desde proveedor real y puede estar inferido o backfilled.",
            )
        )
    if flags.get("timeframe_misaligned"):
        warnings.append(
            SignalDataQualityWarning(
                code="timeframe_misaligned",
                severity=SEVERITY_WARNING,
                message="Los timeframes de las señales base no están perfectamente alineados con el snapshot agregado.",
            )
        )
    return warnings


def build_setup_confirmations(
    setup: dict[str, Any],
    snapshot: dict[str, Any] | None = None,
) -> list[SignalConfirmation]:
    signal_keys = set(_get_value(setup, "signal_keys", []) or [])
    confirmations: list[SignalConfirmation] = []

    volume_24h = _coerce_float((snapshot or {}).get("volume_24h"), 0.0) or 0.0
    avg_volume_24h = _coerce_float((snapshot or {}).get("avg_volume_24h"), 0.0) or 0.0
    volume_ratio = volume_24h / avg_volume_24h if avg_volume_24h > 0 else 0.0
    price_change = abs(_coerce_float((snapshot or {}).get("change_24h"), 0.0) or 0.0)
    momentum = _coerce_float((snapshot or {}).get("momentum_score"), 0.0) or 0.0
    funding_rate = abs(_coerce_float((snapshot or {}).get("funding_rate"), 0.0) or 0.0)
    funding_zscore = abs(_coerce_float((snapshot or {}).get("funding_zscore"), 0.0) or 0.0)
    oi_change = abs(_coerce_float((snapshot or {}).get("oi_change_24h"), 0.0) or 0.0)
    range_high = _coerce_float((snapshot or {}).get("range_high_20d"), 0.0) or 0.0
    range_low = _coerce_float((snapshot or {}).get("range_low_20d"), 0.0) or 0.0
    price = _coerce_float((snapshot or {}).get("price_usd"), 0.0) or 0.0
    long_liquidations = _coerce_float((snapshot or {}).get("long_liquidations_1h"), 0.0) or 0.0
    short_liquidations = _coerce_float((snapshot or {}).get("short_liquidations_1h"), 0.0) or 0.0
    avg_liquidations = _coerce_float((snapshot or {}).get("avg_liquidations_1h"), 0.0) or 0.0

    if "volume_spike" in signal_keys:
        confirmations.append(
            SignalConfirmation(
                label="Volumen anómalo" if volume_ratio >= 1.8 else "Volumen todavía justo para continuación",
                severity=SEVERITY_POSITIVE if volume_ratio >= 1.8 else SEVERITY_WARNING,
            )
        )
    if "range_breakout" in signal_keys:
        breakout_margin = 0.0
        direction = _normalize_direction(_get_value(setup, "direction"))
        if direction == "bullish" and range_high > 0:
            breakout_margin = (price - range_high) / range_high
        elif direction == "bearish" and range_low > 0:
            breakout_margin = (range_low - price) / range_low
        confirmations.append(
            SignalConfirmation(
                label="Expansión direccional confirmada" if breakout_margin >= 0.004 else "Ruptura todavía débil",
                severity=SEVERITY_POSITIVE if breakout_margin >= 0.004 else SEVERITY_WARNING,
            )
        )
    if "funding_extreme" in signal_keys:
        confirmations.append(
            SignalConfirmation(
                label="Funding en extremo" if funding_rate >= 0.02 or funding_zscore >= 2.0 else "Funding todavía neutro",
                severity=SEVERITY_POSITIVE if funding_rate >= 0.02 or funding_zscore >= 2.0 else SEVERITY_WARNING,
            )
        )
    if "liquidation_cluster" in signal_keys:
        total_liquidations = long_liquidations + short_liquidations
        cluster_ratio = total_liquidations / avg_liquidations if avg_liquidations > 0 else 0.0
        confirmations.append(
            SignalConfirmation(
                label="Barrido de liquidaciones" if cluster_ratio >= 2.5 else "Liquidaciones sin cluster claro",
                severity=SEVERITY_POSITIVE if cluster_ratio >= 2.5 else SEVERITY_WARNING,
            )
        )
    if "oi_divergence" in signal_keys:
        divergence = abs(((_coerce_float((snapshot or {}).get("oi_change_24h"), 0.0) or 0.0)) - ((_coerce_float((snapshot or {}).get("change_24h"), 0.0) or 0.0)))
        confirmations.append(
            SignalConfirmation(
                label="Divergencia precio/OI visible" if divergence >= 6.0 else "Divergencia todavía marginal",
                severity=SEVERITY_POSITIVE if divergence >= 6.0 else SEVERITY_WARNING,
            )
        )

    confirmations.append(
        SignalConfirmation(
            label="Momentum acompaña" if momentum >= 70.0 else "Momentum todavía medio",
            severity=SEVERITY_POSITIVE if momentum >= 70.0 else SEVERITY_WARNING,
        )
    )
    confirmations.append(
        SignalConfirmation(
            label="OI acompaña la tesis" if oi_change >= 4.0 else "OI sin confirmación sólida",
            severity=SEVERITY_POSITIVE if oi_change >= 4.0 else SEVERITY_WARNING,
        )
    )
    confirmations.append(
        SignalConfirmation(
            label="Desplazamiento real de precio" if price_change >= 1.0 else "Precio aún sin desplazamiento suficiente",
            severity=SEVERITY_POSITIVE if price_change >= 1.0 else SEVERITY_WARNING,
        )
    )
    return confirmations[:5]


def _indicative_trigger_levels(
    setup: dict[str, Any],
    snapshot: dict[str, Any] | None = None,
) -> tuple[float | None, float | None, float | None, float | None]:
    price = _coerce_float((snapshot or {}).get("price_usd"), None)
    if price is None or price <= 0:
        return None, None, None, None

    direction = _normalize_direction(_get_value(setup, "direction", "neutral"))
    setup_key = str(_get_value(setup, "setup_key", "setup"))
    range_high = _coerce_float((snapshot or {}).get("range_high_20d"), 0.0) or 0.0
    range_low = _coerce_float((snapshot or {}).get("range_low_20d"), 0.0) or 0.0
    range_span = max(range_high - range_low, price * 0.03)
    change_24h = abs(_coerce_float((snapshot or {}).get("change_24h"), 0.0) or 0.0)
    base_buffer = max(price * 0.010, range_span * 0.09, price * min(change_24h / 100.0 * 0.40, 0.03))

    if direction == "bullish":
        if setup_key == "trend_continuation":
            trigger = max(price * 1.002, (range_high * 1.001) if range_high > 0 else price * 1.002)
            invalidation = (range_high - max(range_span * 0.08, price * 0.01)) if range_high > 0 else price - base_buffer
        elif setup_key == "squeeze_reversal":
            trigger = price * 1.004
            invalidation = price - max(base_buffer, range_span * 0.10)
        else:
            trigger = price * 1.003
            invalidation = price - max(base_buffer * 1.1, range_span * 0.11)
        tp1 = trigger + max(price * 0.020, range_span * 0.12)
        tp2 = trigger + max(price * 0.035, range_span * 0.22)
        return trigger, invalidation, tp1, tp2

    if direction == "bearish":
        if setup_key == "trend_continuation":
            trigger = min(price * 0.998, (range_low * 0.999) if range_low > 0 else price * 0.998)
            invalidation = (range_low + max(range_span * 0.08, price * 0.01)) if range_low > 0 else price + base_buffer
        elif setup_key == "squeeze_reversal":
            trigger = price * 0.996
            invalidation = price + max(base_buffer, range_span * 0.10)
        else:
            trigger = price * 0.997
            invalidation = price + max(base_buffer * 1.1, range_span * 0.11)
        tp1 = trigger - max(price * 0.020, range_span * 0.12)
        tp2 = trigger - max(price * 0.035, range_span * 0.22)
        return trigger, invalidation, tp1, tp2

    return None, None, None, None


def build_setup_action_plan(setup: dict[str, Any], snapshot: dict[str, Any] | None = None) -> SignalActionPlan:
    trigger_level, invalidation_level, tp1, tp2 = _indicative_trigger_levels(setup, snapshot)
    direction = _normalize_direction(_get_value(setup, "direction", "neutral"))
    return SignalActionPlan(
        action_now=ACTION_WAIT,
        bias=direction,
        trigger_level=_round_level(trigger_level),
        invalidation_level=_round_level(invalidation_level),
        tp1=_round_level(tp1),
        tp2=_round_level(tp2),
        levels_are_indicative=True,
        note="Niveles indicativos del MVP construidos con precio actual, rango 20d y tipo de setup. No son niveles de ejecución automática.",
    )


def _classify_execution_state(
    setup: dict[str, Any],
    confirmations: list[SignalConfirmation],
    data_quality_warnings: list[SignalDataQualityWarning],
    action_plan: SignalActionPlan,
) -> tuple[str, str, bool]:
    settings = get_settings()
    score = _coerce_float(_get_value(setup, "score"), 0.0) or 0.0
    confidence_pct = _normalize_confidence_pct(_get_value(setup, "confidence"))
    positive_count = sum(item.severity == SEVERITY_POSITIVE for item in confirmations)
    mock_critical = any(item.code in {"mock_contamination", "snapshot_missing"} for item in data_quality_warnings)
    has_levels = action_plan.trigger_level is not None and action_plan.invalidation_level is not None

    if (
        score >= 8.0
        and confidence_pct >= 75.0
        and positive_count >= 2
        and has_levels
        and not (settings.setup_require_no_mock_for_executable and mock_critical)
    ):
        return (
            EXECUTION_EXECUTABLE,
            "La confluencia tiene score alto, confirmaciones suficientes y niveles indicativos utilizables para ejecución táctica.",
            True,
        )

    if score >= 7.2 and confidence_pct >= 65.0 and positive_count >= 2:
        if mock_critical:
            return (
                EXECUTION_WAIT_CONFIRMATION,
                "La confluencia es interesante, pero el contexto está degradado por mock contamination y exige validación adicional.",
                False,
            )
        return (
            EXECUTION_WATCHLIST,
            "La estructura es sólida y merece seguimiento, pero todavía no conviene tratarla como entrada inmediata.",
            False,
        )

    if score >= 6.5 and confidence_pct >= 60.0:
        return (
            EXECUTION_WAIT_CONFIRMATION,
            "El setup tiene interés, pero faltan confirmaciones de flujo o estructura para convertirlo en trade ejecutable.",
            False,
        )

    return (
        EXECUTION_DISCARD,
        "La confluencia no supera el umbral operativo o llega con demasiado ruido para justificar una alerta PRO.",
        False,
    )


def _build_setup_thesis(setup: dict[str, Any]) -> str:
    asset_symbol = str(_get_value(setup, "asset_symbol", "UNKNOWN"))
    direction = _normalize_direction(_get_value(setup, "direction"))
    setup_key = str(_get_value(setup, "setup_key", "setup"))

    if setup_key == "trend_continuation":
        return (
            f"{asset_symbol} alinea volumen anómalo y ruptura de estructura en sesgo {direction}, "
            "una combinación típica de continuación táctica cuando el flujo sigue acompañando."
        )
    if setup_key == "squeeze_reversal":
        return (
            f"{asset_symbol} combina extremo de funding y limpieza de liquidaciones en dirección {direction}, "
            "lo que suele anticipar reversión o squeeze táctico contra el crowd."
        )
    return (
        f"{asset_symbol} presenta divergencia entre precio y open interest, señal de posicionamiento inestable "
        f"que puede terminar en fallo del movimiento y resolución {direction}."
    )


def _summary_from_setup(
    *,
    thesis_short: str,
    execution_reason: str,
    execution_state: str,
    action_plan: SignalActionPlan,
) -> str:
    if execution_state == EXECUTION_EXECUTABLE and action_plan.trigger_level is not None:
        third_sentence = (
            f"Plan base: actuar solo si mantiene trigger indicativo en {action_plan.trigger_level} y respeta la invalidación en {action_plan.invalidation_level}."
        )
    elif execution_state == EXECUTION_WATCHLIST and action_plan.trigger_level is not None:
        third_sentence = f"Plan base: vigilar activación cerca de {action_plan.trigger_level} antes de abrir riesgo."
    elif execution_state == EXECUTION_WAIT_CONFIRMATION:
        third_sentence = "Plan base: esperar confirmación extra de estructura, flujo u open interest antes de actuar."
    else:
        third_sentence = "Plan base: descartar por ahora y reevaluar solo si mejora la confluencia."

    return " ".join([thesis_short, execution_reason, third_sentence])


def _sanitize_for_plan(view: ConfluenceSetupResponse, plan: str) -> ConfluenceSetupResponse:
    normalized_plan = normalize_plan(plan)
    if normalized_plan != PLAN_FREE:
        if normalized_plan == PLAN_PRO_PLUS:
            view.pro_plus_follow_up = SignalProPlusFollowUp(
                status="tracking_reserved",
                note="Reservado para futuras actualizaciones de seguimiento del setup y cambios de estado.",
            )
        return view

    return view.model_copy(
        update={
            "detail_level": "teaser",
            "summary": view.thesis_short or view.thesis,
            "execution_state": None,
            "execution_reason": None,
            "confirmations": [],
            "action_plan": None,
            "data_quality_warnings": [],
            "key_data": None,
            "is_trade_executable": False,
            "pro_plus_follow_up": None,
        }
    )


def build_setup_view(
    setup: dict[str, Any],
    snapshot: dict[str, Any] | None = None,
    *,
    plan: str = PLAN_FREE,
) -> ConfluenceSetupResponse:
    headline = f"{_get_value(setup, 'asset_symbol', 'UNKNOWN')} — {_get_value(setup, 'setup_type', 'Setup')}"
    thesis = str(_get_value(setup, "thesis") or _build_setup_thesis(setup))
    thesis_short = _extract_first_sentence(thesis)
    confirmations = build_setup_confirmations(setup, snapshot)
    data_quality_warnings = build_setup_data_quality_warnings(setup, snapshot)
    action_plan = build_setup_action_plan(setup, snapshot)
    execution_state, execution_reason, is_trade_executable = _classify_execution_state(
        setup,
        confirmations,
        data_quality_warnings,
        action_plan,
    )

    if execution_state == EXECUTION_EXECUTABLE:
        action_plan.action_now = ACTION_ENTER
    elif execution_state in {EXECUTION_WATCHLIST, EXECUTION_WAIT_CONFIRMATION}:
        action_plan.action_now = ACTION_WAIT
    else:
        action_plan.action_now = ACTION_DISCARD

    generated_at = _get_value(setup, "generated_at", datetime.now(timezone.utc))
    if isinstance(generated_at, str):
        generated_at = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))

    view = ConfluenceSetupResponse(
        setup_key=str(_get_value(setup, "setup_key", "setup")),
        setup_type=str(_get_value(setup, "setup_type", "Setup")),
        asset_symbol=str(_get_value(setup, "asset_symbol", "UNKNOWN")),
        direction=_normalize_direction(_get_value(setup, "direction", "neutral")),
        signal_keys=[str(item) for item in list(_get_value(setup, "signal_keys", []))],
        signals=[
            SetupSignalComponent(
                signal_key=str(_get_value(signal, "signal_key", "signal")),
                signal_type=str(_get_value(signal, "signal_type", _get_value(signal, "signal_key", "Signal"))),
                direction=_normalize_direction(_get_value(signal, "direction", "neutral")),
                score=round(_coerce_float(_get_value(signal, "score"), 0.0) or 0.0, 1),
                confidence=_normalize_confidence_pct(_get_value(signal, "confidence")),
            )
            for signal in list(_get_value(setup, "signals", []))
        ],
        headline=headline,
        execution_state=execution_state,
        execution_reason=execution_reason,
        summary=_summary_from_setup(
            thesis_short=thesis_short,
            execution_reason=execution_reason,
            execution_state=execution_state,
            action_plan=action_plan,
        ),
        thesis=thesis,
        thesis_short=thesis_short,
        score=round(_coerce_float(_get_value(setup, "score"), 0.0) or 0.0, 1),
        confidence=_normalize_confidence_pct(_get_value(setup, "confidence")),
        model_score=round(_coerce_float(_get_value(setup, "score"), 0.0) or 0.0, 1),
        confidence_pct=_normalize_confidence_pct(_get_value(setup, "confidence")),
        key_data=_build_key_data(snapshot),
        confirmations=confirmations,
        action_plan=action_plan,
        data_quality_warnings=data_quality_warnings,
        is_mock_contaminated=any(
            warning.code in {"mock_contamination", "snapshot_missing"} for warning in data_quality_warnings
        ),
        is_trade_executable=is_trade_executable,
        generated_at=generated_at,
        source_snapshot_time=(snapshot or {}).get("captured_at") or _get_value(setup, "source_snapshot_time"),
    )
    return _sanitize_for_plan(view, plan)


def build_setup_views(
    setups: list[dict[str, Any]],
    market_snapshots: list[dict[str, Any]] | None = None,
    *,
    plan: str = PLAN_FREE,
) -> list[ConfluenceSetupResponse]:
    snapshot_index = {
        str(snapshot.get("symbol", "")).upper(): snapshot
        for snapshot in (market_snapshots or [])
    }
    views = [
        build_setup_view(
            setup,
            snapshot_index.get(str(_get_value(setup, "asset_symbol", "")).upper()),
            plan=plan,
        )
        for setup in setups
    ]
    views.sort(key=lambda setup: (setup.score, setup.confidence), reverse=True)
    return views
