from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.schemas import (
    ProSignalResponse,
    SignalActionPlan,
    SignalConfirmation,
    SignalDataQualityWarning,
    SignalKeyData,
    SignalProPlusFollowUp,
)
from services.plans import PLAN_FREE, PLAN_PRO_PLUS, normalize_plan

EXECUTION_EXECUTABLE = "EXECUTABLE"
EXECUTION_WATCHLIST = "WATCHLIST"
EXECUTION_WAIT_CONFIRMATION = "WAIT_CONFIRMATION"
EXECUTION_DISCARD = "DISCARD"

SEVERITY_POSITIVE = "positive"
SEVERITY_WARNING = "warning"
SEVERITY_NEGATIVE = "negative"

ACTION_ENTER = "enter"
ACTION_WAIT = "wait"
ACTION_DISCARD = "discard"


def _get_value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_confidence_pct(value: Any) -> float:
    numeric = _coerce_float(value)
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


def _snapshot_source(signal: Any, snapshot: dict[str, Any] | None) -> str:
    return str((snapshot or {}).get("source") or _get_value(signal, "source", "runtime"))


def _source_contains_mock(signal: Any, snapshot: dict[str, Any] | None) -> bool:
    return "mock" in _snapshot_source(signal, snapshot).lower()


def _extract_first_sentence(text: str, max_length: int = 160) -> str:
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


def _build_key_data(signal: Any, snapshot: dict[str, Any] | None) -> SignalKeyData:
    source = _snapshot_source(signal, snapshot)
    return SignalKeyData(
        price=_coerce_float((snapshot or {}).get("price_usd"), None),
        change_24h=_coerce_float((snapshot or {}).get("change_24h"), None),
        volume_24h=_coerce_float((snapshot or {}).get("volume_24h"), None),
        funding=_coerce_float((snapshot or {}).get("funding_rate"), None),
        oi_change_24h=_coerce_float((snapshot or {}).get("oi_change_24h"), None),
        timeframe_base=str((snapshot or {}).get("timeframe", "1D")),
        source=source,
    )


def build_data_quality_warnings(signal: Any, snapshot: dict[str, Any] | None) -> list[SignalDataQualityWarning]:
    warnings: list[SignalDataQualityWarning] = []
    signal_key = str(_get_value(signal, "signal_key", "signal"))
    raw_payload = (snapshot or {}).get("raw_payload") or {}

    if snapshot is None:
        warnings.append(
            SignalDataQualityWarning(
                code="snapshot_missing",
                severity=SEVERITY_NEGATIVE,
                message="No hay snapshot enlazado a esta señal. La lectura operativa queda degradada.",
            )
        )

    if _source_contains_mock(signal, snapshot):
        warnings.append(
            SignalDataQualityWarning(
                code="mock_contamination",
                severity=SEVERITY_NEGATIVE,
                message="Parte del contexto usa fallback mock o defaults del MVP. No la trates como setup fully validated.",
            )
        )

    has_real_oi = bool(
        raw_payload.get("bybit", {}).get("open_interest") or raw_payload.get("binance", {}).get("open_interest")
    )
    if snapshot is not None and not has_real_oi:
        warnings.append(
            SignalDataQualityWarning(
                code="oi_inferred",
                severity=SEVERITY_WARNING,
                message="El open interest no llega completo desde proveedor real y puede estar inferido o backfilled.",
            )
        )

    has_real_liquidations = bool(raw_payload.get("coinglass", {}).get("liquidations"))
    if signal_key == "liquidation_cluster" and not has_real_liquidations:
        warnings.append(
            SignalDataQualityWarning(
                code="liquidations_unverified",
                severity=SEVERITY_WARNING,
                message="La lectura de liquidaciones no viene de un feed dedicado completo en este entorno.",
            )
        )

    signal_timeframe = str(_get_value(signal, "timeframe", "")).upper()
    snapshot_timeframe = str((snapshot or {}).get("timeframe", "")).upper()
    if signal_timeframe and snapshot_timeframe and signal_timeframe != snapshot_timeframe:
        warnings.append(
            SignalDataQualityWarning(
                code="timeframe_misaligned",
                severity=SEVERITY_WARNING,
                message="El timeframe de la señal no está perfectamente alineado con el snapshot base usado para resumirla.",
            )
        )

    return warnings


def build_pro_confirmations(signal: Any, snapshot: dict[str, Any] | None) -> list[SignalConfirmation]:
    confirmations: list[SignalConfirmation] = []
    signal_key = str(_get_value(signal, "signal_key", "signal"))
    direction = _normalize_direction(_get_value(signal, "direction", "neutral"))
    price_change = _coerce_float((snapshot or {}).get("change_24h"))
    volume_24h = _coerce_float((snapshot or {}).get("volume_24h"))
    avg_volume_24h = _coerce_float((snapshot or {}).get("avg_volume_24h"))
    volume_ratio = volume_24h / avg_volume_24h if avg_volume_24h > 0 else 0.0
    momentum = _coerce_float((snapshot or {}).get("momentum_score"))
    funding_rate = abs(_coerce_float((snapshot or {}).get("funding_rate")))
    funding_zscore = abs(_coerce_float((snapshot or {}).get("funding_zscore")))
    oi_change = _coerce_float((snapshot or {}).get("oi_change_24h"))
    price = _coerce_float((snapshot or {}).get("price_usd"))
    range_high = _coerce_float((snapshot or {}).get("range_high_20d"))
    range_low = _coerce_float((snapshot or {}).get("range_low_20d"))
    long_liquidations = _coerce_float((snapshot or {}).get("long_liquidations_1h"))
    short_liquidations = _coerce_float((snapshot or {}).get("short_liquidations_1h"))
    avg_liquidations = _coerce_float((snapshot or {}).get("avg_liquidations_1h"))

    if signal_key == "volume_spike":
        confirmations.append(
            SignalConfirmation(
                label="Volumen anómalo",
                severity=SEVERITY_POSITIVE if volume_ratio >= 1.8 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Expansión direccional",
                severity=SEVERITY_POSITIVE if abs(price_change) >= 1.5 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="OI acompaña el movimiento" if abs(oi_change) >= 4.0 else "OI sin confirmación clara",
                severity=SEVERITY_POSITIVE if abs(oi_change) >= 4.0 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Momentum consistente" if momentum >= 70.0 else "Momentum todavía medio",
                severity=SEVERITY_POSITIVE if momentum >= 70.0 else SEVERITY_WARNING,
            )
        )

    elif signal_key == "range_breakout":
        breakout_margin = 0.0
        if direction == "bullish" and range_high > 0:
            breakout_margin = (price - range_high) / range_high
        elif direction == "bearish" and range_low > 0:
            breakout_margin = (range_low - price) / range_low

        confirmations.append(
            SignalConfirmation(
                label="Ruptura real del rango 20d" if breakout_margin >= 0.004 else "Ruptura todavía débil",
                severity=SEVERITY_POSITIVE if breakout_margin >= 0.004 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Volumen acompaña la ruptura" if volume_ratio >= 1.2 else "Volumen todavía justo",
                severity=SEVERITY_POSITIVE if volume_ratio >= 1.2 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="OI confirma expansión" if abs(oi_change) >= 3.0 else "OI plano para breakout",
                severity=SEVERITY_POSITIVE if abs(oi_change) >= 3.0 else SEVERITY_WARNING,
            )
        )

    elif signal_key == "funding_extreme":
        confirmations.append(
            SignalConfirmation(
                label="Funding en extremo",
                severity=SEVERITY_POSITIVE if funding_rate >= 0.02 or funding_zscore >= 2.0 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="OI confirma crowded positioning" if abs(oi_change) >= 4.0 else "OI aún no confirma el crowded trade",
                severity=SEVERITY_POSITIVE if abs(oi_change) >= 4.0 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="El precio ya reacciona al desequilibrio" if abs(price_change) >= 1.0 else "Precio todavía neutro frente al exceso",
                severity=SEVERITY_POSITIVE if abs(price_change) >= 1.0 else SEVERITY_WARNING,
            )
        )

    elif signal_key == "oi_divergence":
        divergence = abs(oi_change - price_change)
        confirmations.append(
            SignalConfirmation(
                label="Divergencia visible entre precio y OI" if divergence >= 6.0 else "Divergencia todavía marginal",
                severity=SEVERITY_POSITIVE if divergence >= 6.0 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Posicionamiento desequilibrado" if abs(oi_change) >= 6.0 else "OI aún sin exceso claro",
                severity=SEVERITY_POSITIVE if abs(oi_change) >= 6.0 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Precio ya hace barrido contra la dirección previa"
                if (direction == "bullish" and price_change < 0) or (direction == "bearish" and price_change > 0)
                else "Precio todavía no limpia suficiente estructura",
                severity=SEVERITY_POSITIVE
                if (direction == "bullish" and price_change < 0) or (direction == "bearish" and price_change > 0)
                else SEVERITY_WARNING,
            )
        )

    elif signal_key == "liquidation_cluster":
        total_liquidations = long_liquidations + short_liquidations
        cluster_ratio = total_liquidations / avg_liquidations if avg_liquidations > 0 else 0.0
        dominance = max(long_liquidations, short_liquidations) / total_liquidations if total_liquidations > 0 else 0.0

        confirmations.append(
            SignalConfirmation(
                label="Cluster de liquidaciones",
                severity=SEVERITY_POSITIVE if cluster_ratio >= 2.5 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Limpieza concentrada en una sola banda" if dominance >= 0.68 else "Liquidación sin dominancia clara",
                severity=SEVERITY_POSITIVE if dominance >= 0.68 else SEVERITY_WARNING,
            )
        )
        confirmations.append(
            SignalConfirmation(
                label="Movimiento con desplazamiento real" if abs(price_change) >= 0.5 else "Barrido con poco desplazamiento",
                severity=SEVERITY_POSITIVE if abs(price_change) >= 0.5 else SEVERITY_WARNING,
            )
        )

    if not confirmations:
        for evidence in list(_get_value(signal, "evidence", []))[:3]:
            confirmations.append(
                SignalConfirmation(
                    label=str(evidence),
                    severity=SEVERITY_WARNING,
                )
            )

    return confirmations


def _indicative_trigger_levels(signal: Any, snapshot: dict[str, Any] | None) -> tuple[float | None, float | None, float | None, float | None]:
    price = _coerce_float((snapshot or {}).get("price_usd"), None)
    if price is None or price <= 0:
        return None, None, None, None

    direction = _normalize_direction(_get_value(signal, "direction", "neutral"))
    range_high = _coerce_float((snapshot or {}).get("range_high_20d"))
    range_low = _coerce_float((snapshot or {}).get("range_low_20d"))
    range_span = max(range_high - range_low, price * 0.03)
    change_24h = abs(_coerce_float((snapshot or {}).get("change_24h")))
    base_buffer = max(price * 0.008, range_span * 0.08, price * min(change_24h / 100.0 * 0.35, 0.03))
    signal_key = str(_get_value(signal, "signal_key", "signal"))

    if direction == "bullish":
        if signal_key == "range_breakout" and range_high > 0:
            trigger = max(price, range_high * 1.001)
            invalidation = range_high - max(range_span * 0.10, price * 0.012)
        else:
            trigger = price * 1.003
            invalidation = price - base_buffer
        tp1 = trigger + max(price * 0.018, range_span * 0.12)
        tp2 = trigger + max(price * 0.032, range_span * 0.22)
        return trigger, invalidation, tp1, tp2

    if direction == "bearish":
        if signal_key == "range_breakout" and range_low > 0:
            trigger = min(price, range_low * 0.999)
            invalidation = range_low + max(range_span * 0.10, price * 0.012)
        else:
            trigger = price * 0.997
            invalidation = price + base_buffer
        tp1 = trigger - max(price * 0.018, range_span * 0.12)
        tp2 = trigger - max(price * 0.032, range_span * 0.22)
        return trigger, invalidation, tp1, tp2

    return None, None, None, None


def build_action_plan(signal: Any, snapshot: dict[str, Any] | None) -> SignalActionPlan:
    trigger_level, invalidation_level, tp1, tp2 = _indicative_trigger_levels(signal, snapshot)
    direction = _normalize_direction(_get_value(signal, "direction", "neutral"))
    return SignalActionPlan(
        action_now=ACTION_WAIT,
        bias=direction,
        trigger_level=_round_level(trigger_level),
        invalidation_level=_round_level(invalidation_level),
        tp1=_round_level(tp1),
        tp2=_round_level(tp2),
        levels_are_indicative=True,
        note="Niveles indicativos del MVP basados en precio actual y rango 20d. No son niveles de ejecución automática.",
    )


def _classify_execution_state(
    signal: Any,
    confirmations: list[SignalConfirmation],
    data_quality_warnings: list[SignalDataQualityWarning],
    action_plan: SignalActionPlan,
) -> tuple[str, str, bool]:
    score = _coerce_float(_get_value(signal, "score"))
    confidence_pct = _normalize_confidence_pct(_get_value(signal, "confidence"))
    positive_count = sum(item.severity == SEVERITY_POSITIVE for item in confirmations)
    negative_count = sum(item.severity == SEVERITY_NEGATIVE for item in confirmations)
    mock_critical = any(item.code in {"mock_contamination", "snapshot_missing"} for item in data_quality_warnings)
    has_levels = action_plan.trigger_level is not None and action_plan.invalidation_level is not None

    if score >= 8.0 and confidence_pct >= 75.0 and not mock_critical and positive_count >= 2 and has_levels and negative_count == 0:
        return (
            EXECUTION_EXECUTABLE,
            "Score alto, confirmaciones suficientes y niveles indicativos disponibles. Sigue siendo una ejecución táctica, no automática.",
            True,
        )

    if score < 6.0 or confidence_pct < 55.0 or negative_count >= 2:
        return (
            EXECUTION_DISCARD,
            "La señal no supera el umbral operativo o llega con demasiado ruido para tomar riesgo ahora.",
            False,
        )

    if score >= 7.3 and confidence_pct >= 65.0 and positive_count >= 2 and has_levels:
        if mock_critical:
            return (
                EXECUTION_WAIT_CONFIRMATION,
                "La tesis existe, pero el dato está contaminado por fallback mock y exige validación adicional antes de actuar.",
                False,
            )
        return (
            EXECUTION_WATCHLIST,
            "Hay estructura suficiente para seguirla, pero todavía no conviene tratarla como entrada inmediata.",
            False,
        )

    if score >= 6.5 and confidence_pct >= 60.0:
        return (
            EXECUTION_WAIT_CONFIRMATION,
            "La señal tiene interés, pero faltan confirmaciones de flujo o estructura para convertirla en trade ejecutable.",
            False,
        )

    return (
        EXECUTION_DISCARD,
        "La lectura es demasiado débil o degradada para sostener una señal PRO accionable.",
        False,
    )


def _summary_from_signal(
    *,
    thesis_short: str,
    execution_reason: str,
    execution_state: str,
    action_plan: SignalActionPlan,
) -> str:
    if execution_state == EXECUTION_EXECUTABLE and action_plan.trigger_level is not None:
        third_sentence = (
            f"Plan base: entrada solo si mantiene el trigger indicativo en {action_plan.trigger_level} y respeta la invalidación en {action_plan.invalidation_level}."
        )
    elif execution_state == EXECUTION_WATCHLIST and action_plan.trigger_level is not None:
        third_sentence = f"Plan base: vigilar activación cerca de {action_plan.trigger_level} antes de abrir riesgo."
    elif execution_state == EXECUTION_WAIT_CONFIRMATION:
        third_sentence = "Plan base: esperar confirmación extra de flujo, estructura u open interest antes de actuar."
    else:
        third_sentence = "Plan base: descartar por ahora y reevaluar solo si mejora la estructura."

    return " ".join([thesis_short, execution_reason, third_sentence])


def _teaser_summary(signal_type: str, thesis_short: str) -> str:
    return f"{signal_type}: {thesis_short}"


def _sanitize_for_plan(view: ProSignalResponse, plan: str) -> ProSignalResponse:
    normalized_plan = normalize_plan(plan)
    if normalized_plan != PLAN_FREE:
        if normalized_plan == PLAN_PRO_PLUS:
            view.pro_plus_follow_up = SignalProPlusFollowUp(
                status="tracking_reserved",
                note="Reservado para futuras actualizaciones de seguimiento y cambios de estado.",
            )
        return view

    return view.model_copy(
        update={
            "detail_level": "teaser",
            "summary": _teaser_summary(view.signal_type, view.thesis_short or view.thesis),
            "thesis": view.thesis_short or view.thesis,
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


def build_pro_signal_view(
    signal: Any,
    snapshot: dict[str, Any] | None = None,
    *,
    plan: str = PLAN_FREE,
) -> ProSignalResponse:
    headline = f"{_get_value(signal, 'asset_symbol', 'UNKNOWN')} — {_get_value(signal, 'signal_type', 'Signal')}"
    thesis_short = _extract_first_sentence(str(_get_value(signal, "thesis", "Sin tesis disponible")))
    confirmations = build_pro_confirmations(signal, snapshot)
    data_quality_warnings = build_data_quality_warnings(signal, snapshot)
    action_plan = build_action_plan(signal, snapshot)
    execution_state, execution_reason, is_trade_executable = _classify_execution_state(
        signal,
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

    source_snapshot_time = (snapshot or {}).get("captured_at") or _get_value(signal, "source_snapshot_time")
    pro_view = ProSignalResponse(
        id=str(_get_value(signal, "id")),
        signal_key=str(_get_value(signal, "signal_key", "signal")),
        asset_symbol=str(_get_value(signal, "asset_symbol", "UNKNOWN")),
        signal_type=str(_get_value(signal, "signal_type", _get_value(signal, "signal_key", "Signal"))),
        timeframe=str(_get_value(signal, "timeframe", "4H")),
        direction=_normalize_direction(_get_value(signal, "direction", "neutral")),
        confidence=_normalize_confidence_pct(_get_value(signal, "confidence")),
        score=round(_coerce_float(_get_value(signal, "score")), 1),
        thesis=str(_get_value(signal, "thesis", "")),
        evidence=[str(item) for item in list(_get_value(signal, "evidence", _get_value(signal, "evidence_json", [])) or [])],
        source=_snapshot_source(signal, snapshot),
        generated_at=_get_value(signal, "generated_at", _get_value(signal, "created_at", datetime.now(timezone.utc))),
        headline=headline,
        execution_state=execution_state,
        execution_reason=execution_reason,
        summary=_summary_from_signal(
            thesis_short=thesis_short,
            execution_reason=execution_reason,
            execution_state=execution_state,
            action_plan=action_plan,
        ),
        model_score=round(_coerce_float(_get_value(signal, "score")), 1),
        confidence_pct=_normalize_confidence_pct(_get_value(signal, "confidence")),
        thesis_short=thesis_short,
        key_data=_build_key_data(signal, snapshot),
        confirmations=confirmations,
        action_plan=action_plan,
        data_quality_warnings=data_quality_warnings,
        is_mock_contaminated=any(item.code == "mock_contamination" for item in data_quality_warnings),
        is_trade_executable=is_trade_executable,
        detail_level="full",
        source_snapshot_time=source_snapshot_time,
    )
    return _sanitize_for_plan(pro_view, plan)


def build_pro_signal_views(
    signals: list[Any],
    market_snapshots: list[dict[str, Any]] | None = None,
    *,
    plan: str = PLAN_FREE,
) -> list[ProSignalResponse]:
    snapshot_index = {
        str(snapshot["symbol"]).upper(): snapshot
        for snapshot in (market_snapshots or [])
    }
    return [
        build_pro_signal_view(
            signal,
            snapshot_index.get(str(_get_value(signal, "asset_symbol", "")).upper()),
            plan=plan,
        )
        for signal in signals
    ]
