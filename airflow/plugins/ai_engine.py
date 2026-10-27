"""
SismoWatch AI & Analytics Engine.
Calculates deterministic KPIs, performs spatial & magnitude anomaly detection,
sanitizes external texts against Prompt Injection, generates executive reports
via LLM (with deterministic template fallback), and validates factual consistency.
"""

import os
import re
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


def sanitize_text(text: str | None, max_len: int = 150) -> str:
    """
    Sanitizes external text strings (e.g. properties.place) to prevent Prompt Injection
    and delimiter escaping when fed into LLM prompts.
    """
    if not text:
        return "Unknown Region"
    
    # Strip dangerous markdown, delimiter tags and prompt injection keywords
    sanitized = re.sub(r"[\r\n\t]+", " ", str(text))
    # Remove characters often used in jailbreaking/markdown breaking
    sanitized = re.sub(r"[`<>{}\[\]\\]", "", sanitized)
    # Neutralize instruction injection phrases
    injection_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions?",
        r"(?i)system\s*prompt",
        r"(?i)you\s+are\s+now",
        r"(?i)new\s+rule",
        r"(?i)as\s+an\s+ai\s+language\s+model",
        r"(?i)override"
    ]
    for pattern in injection_patterns:
        sanitized = re.sub(pattern, "[FILTERED]", sanitized)
    
    # Trim length
    sanitized = sanitized.strip()[:max_len]
    return sanitized if sanitized else "Unknown Region"


def calculate_deterministic_kpis(events_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes exact mathematical KPIs for a given set of earthquake records.
    Never hallucinates or guesses.
    """
    if events_df is None or events_df.empty:
        return {
            "total_events": 0,
            "max_magnitude": 0.0,
            "avg_magnitude": 0.0,
            "min_magnitude": 0.0,
            "tsunami_alerts": 0,
            "most_active_region": "Sin actividad registrada",
            "avg_depth_km": 0.0,
            "max_depth_km": 0.0
        }

    df = events_df.copy()
    total_events = int(len(df))
    max_mag = float(df["mag"].max()) if "mag" in df and not df["mag"].isna().all() else 0.0
    min_mag = float(df["mag"].min()) if "mag" in df and not df["mag"].isna().all() else 0.0
    avg_mag = float(df["mag"].mean()) if "mag" in df and not df["mag"].isna().all() else 0.0
    tsunami_alerts = int((df["tsunami"] > 0).sum()) if "tsunami" in df else 0
    avg_depth = float(df["depth_km"].mean()) if "depth_km" in df and not df["depth_km"].isna().all() else 0.0
    max_depth = float(df["depth_km"].max()) if "depth_km" in df and not df["depth_km"].isna().all() else 0.0

    # Determine most active general region (sanitized)
    if "place" in df and not df["place"].isna().all():
        # USGS places typically format as 'XX km NNW of Location, State/Country'
        regions = df["place"].dropna().apply(lambda p: sanitize_text(p.split(" of ")[-1] if " of " in p else p))
        top_region = regions.value_counts().index[0] if not regions.empty else "Global"
    else:
        top_region = "Global"

    return {
        "total_events": total_events,
        "max_magnitude": round(max_mag, 2),
        "min_magnitude": round(min_mag, 2),
        "avg_magnitude": round(avg_mag, 2),
        "tsunami_alerts": tsunami_alerts,
        "most_active_region": top_region,
        "avg_depth_km": round(avg_depth, 2),
        "max_depth_km": round(max_depth, 2)
    }


def detect_seismic_anomalies(events_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detects seismic swarms, anomalous high magnitudes, or unusual depth patterns
    using statistical thresholding and IsolationForest unsupervised clustering.
    """
    anomalies: List[Dict[str, Any]] = []
    if events_df is None or len(events_df) == 0:
        return anomalies

    df = events_df.copy()
    now_utc = datetime.now(timezone.utc)

    # 1. Rule-based Critical Magnitude Alert (Mag >= 6.0)
    high_mag_events = df[df["mag"] >= 6.0]
    for _, row in high_mag_events.iterrows():
        anomalies.append({
            "detected_at": now_utc.isoformat(),
            "anomaly_type": "HIGH_MAGNITUDE_EVENT",
            "metric_trigger": f"Magnitude {row['mag']} >= 6.0 threshold",
            "description": f"Sismo de magnitud significativa ({row['mag']}) registrado en {sanitize_text(row.get('place'))}.",
            "event_ids": [str(row.get("id"))]
        })

    # 2. Rule-based Tsunami Alert Trigger
    if "tsunami" in df:
        tsunami_events = df[df["tsunami"] > 0]
        for _, row in tsunami_events.iterrows():
            anomalies.append({
                "detected_at": now_utc.isoformat(),
                "anomaly_type": "TSUNAMI_WARNING_TRIGGERED",
                "metric_trigger": "tsunami_flag == 1",
                "description": f"Alerta de tsunami emitida para sismo en {sanitize_text(row.get('place'))} (M {row['mag']}).",
                "event_ids": [str(row.get("id"))]
            })

    # 3. Spatial Swarm Detection (Unusual concentration of events in a single area)
    if "place" in df and len(df) >= 5:
        # Group by approximate region
        regions = df["place"].dropna().apply(lambda p: sanitize_text(p.split(" of ")[-1] if " of " in p else p))
        counts = regions.value_counts()
        # If any region has > 25% of all events and count >= 5
        for reg_name, count in counts.items():
            if count >= 5 and (count / len(df)) >= 0.20:
                cluster_events = df[regions == reg_name]
                anomalies.append({
                    "detected_at": now_utc.isoformat(),
                    "anomaly_type": "SEISMIC_SWARM_CLUSTER",
                    "metric_trigger": f"{count} eventos concentrados en {reg_name} ({count / len(df) * 100:.1f}% del total)",
                    "description": f"Posible enjambre sísmico detectado en {reg_name} con {count} sismos en la ventana analizada.",
                    "event_ids": cluster_events["id"].astype(str).tolist()[:20]
                })

    # 4. IsolationForest for Multivariate Outliers (Mag, Depth, Lat, Lon)
    feature_cols = ["mag", "depth_km", "latitude", "longitude"]
    valid_df = df.dropna(subset=feature_cols)
    if len(valid_df) >= 15:
        try:
            X = valid_df[feature_cols].values
            iso = IsolationForest(contamination=0.05, random_state=42)
            preds = iso.fit_predict(X)
            outlier_rows = valid_df[preds == -1]

            if not outlier_rows.empty:
                for _, out in outlier_rows.iterrows():
                    # Only report if it wasn't already caught by high magnitude rule
                    if out["mag"] < 6.0:
                        anomalies.append({
                            "detected_at": now_utc.isoformat(),
                            "anomaly_type": "MULTIVARIATE_OUTLIER",
                            "metric_trigger": f"IsolationForest outlier (Depth: {out['depth_km']}km, Mag: {out['mag']})",
                            "description": f"Patrón atípico de profundidad/magnitud ({out['depth_km']} km, M {out['mag']}) en {sanitize_text(out.get('place'))}.",
                            "event_ids": [str(out["id"])]
                        })
        except Exception:
            pass  # Fallback gracefully if matrix is singular or data is homogeneous

    return anomalies


def build_deterministic_narrative(
    report_date: str,
    kpis: Dict[str, Any],
    anomalies: List[Dict[str, Any]]
) -> str:
    """
    Generates a rigorous, professional narrative report strictly based on calculated KPIs
    without any hallucination. Used as primary or fallback reporter.
    """
    total = kpis["total_events"]
    max_m = kpis["max_magnitude"]
    avg_m = kpis["avg_magnitude"]
    tsunami = kpis["tsunami_alerts"]
    region = kpis["most_active_region"]
    avg_depth = kpis["avg_depth_km"]

    if total == 0:
        return (
            f"### Informe Ejecutivo Sísmico Diario ({report_date})\n\n"
            f"**Resumen Operativo:** Durante las últimas 24 horas no se registraron eventos sísmicos en la red analizada. "
            f"El catálogo operó sin anomalías detectadas y los sensores reportan estabilidad global."
        )

    tsunami_clause = (
        f"Se emitieron **{tsunami} alertas de tsunami** que requieren supervisión continua por los organismos costeros de emergencia."
        if tsunami > 0
        else "No se registraron alertas de tsunami durante el período analizado."
    )

    anomalies_clause = ""
    if anomalies:
        anomalies_clause = "\n\n#### Detección de Anomalías y Enjambres:\n"
        for idx, a in enumerate(anomalies[:5], start=1):
            anomalies_clause += f"- **[{a['anomaly_type']}]** {a['description']} *(Disparador: {a['metric_trigger']})*\n"
    else:
        anomalies_clause = "\n\n#### Detección de Anomalías:\n- No se identificaron anomalías estadísticas ni enjambres críticos en el ciclo diario."

    narrative = (
        f"### Informe Ejecutivo Sísmico Diario — SismoWatch ({report_date})\n\n"
        f"**1. Panorama General de Actividad:**\n"
        f"Durante la ventana de observación de 24 horas, la red global USGS registró un total consolidado de **{total} eventos sísmicos**. "
        f"La magnitud promedio del período se situó en **{avg_m}**, alcanzando una magnitud máxima de **{max_m}**. "
        f"La profundidad promedio observada fue de **{avg_depth} km**.\n\n"
        f"**2. Región de Mayor Actividad:**\n"
        f"El sector geográfico con mayor concentración sísmica fue **{region}**, agrupando la mayor densidad de réplicas y micro-sismos.\n\n"
        f"**3. Protocolos de Seguridad y Alertas:**\n"
        f"{tsunami_clause}"
        f"{anomalies_clause}\n\n"
        f"*Informe generado automáticamente mediante el motor analítico determinista de SismoWatch.*"
    )
    return narrative


def verify_factual_consistency(
    narrative: str,
    kpis: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Golden Rule Fact-Checker:
    Checks if numbers cited in narrative match the computed KPIs.
    """
    discrepancies = []
    
    # Check total events citation if present
    total_str = str(kpis["total_events"])
    if total_str not in narrative and kpis["total_events"] > 0:
        discrepancies.append(f"Narrative does not cite exact total events: {total_str}")

    # Check max magnitude citation
    max_mag_str = str(kpis["max_magnitude"])
    if max_mag_str not in narrative and kpis["max_magnitude"] > 0:
        discrepancies.append(f"Narrative does not cite exact max magnitude: {max_mag_str}")

    return (len(discrepancies) == 0, discrepancies)


def generate_ai_report(
    report_date: str,
    kpis: Dict[str, Any],
    anomalies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Orchestrates report generation: tries LLM with strict grounding prompt;
    if LLM API is unavailable, fails, or hallucinates, uses deterministic fallback template.
    """
    start_time = time.time()
    api_key = os.environ.get("OPENAI_API_KEY")
    model_name = "sismowatch-deterministic-engine"
    tokens_used = 0

    if api_key and api_key.startswith("sk-"):
        try:
            import httpx
            # Call OpenAI or compatible API
            prompt_content = f"""
Eres el analista jefe de sismología de SismoWatch.
Redacta un informe ejecutivo profesional para el día {report_date}.
REGLA ESTRICTA: Basa tu informe ÚNICA Y EXCLUSIVAMENTE en los siguientes datos calculados.
No inventes ningún número ni alteres las cifras bajo ninguna circunstancia.

KPIs Deterministas:
- Total eventos: {kpis['total_events']}
- Magnitud máxima: {kpis['max_magnitude']}
- Magnitud promedio: {kpis['avg_magnitude']}
- Alertas de tsunami: {kpis['tsunami_alerts']}
- Región más activa: {kpis['most_active_region']}
- Profundidad promedio: {kpis['avg_depth_km']} km

Anomalías Detectadas:
{json.dumps(anomalies, indent=2, ensure_ascii=False)}

Incluye:
1. Resumen Ejecutivo (citando exactamente {kpis['total_events']} eventos y magnitud máxima {kpis['max_magnitude']}).
2. Análisis de la región más activa ({kpis['most_active_region']}).
3. Estado de alertas y anomalías detectadas.
"""
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Eres un asistente de datos sismológicos de alta precisión."},
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": 0.1
            }

            resp = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20.0)
            if resp.status_code == 200:
                result = resp.json()
                raw_narrative = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                model_name = "gpt-4o-mini"

                # Fact-check validation
                is_valid, _ = verify_factual_consistency(raw_narrative, kpis)
                if is_valid:
                    latency = round(time.time() - start_time, 2)
                    return {
                        "narrative_text": raw_narrative,
                        "structured_kpis": kpis,
                        "model_name": model_name,
                        "tokens_used": tokens_used,
                        "latency_sec": latency
                    }
        except Exception:
            pass  # Fall through to deterministic generator on any network or API issue

    # Deterministic high-quality generator
    narrative = build_deterministic_narrative(report_date, kpis, anomalies)
    latency = round(time.time() - start_time, 2)

    return {
        "narrative_text": narrative,
        "structured_kpis": kpis,
        "model_name": model_name,
        "tokens_used": tokens_used,
        "latency_sec": latency
    }
