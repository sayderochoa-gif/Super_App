"""Conversational AI Agent for seismic analysis, SQL synthesis, and tool execution."""

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from openai import OpenAI
from agentebot.config import settings
from agentebot.agent.tools import (
    OPENAI_TOOLS,
    TOOL_DISPATCHER,
    get_database_schema,
    get_seismic_statistics,
    query_earthquakes,
    sync_realtime_earthquakes,
    get_tsunami_alerts,
    execute_safe_sql,
)
from agentebot.agent.knowledge import (
    query_seismic_knowledge,
    sanitize_response,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are 'SeismoAgent', an expert Senior Seismologist, Relational Data Analyst, and Disaster Prevention Specialist.
Your mission is to provide accurate seismic monitoring, real-time telemetry analysis, SQL querying, and comprehensive public education on earthquake prevention and civil protection.

You have access to a normalized relational database containing real-time USGS earthquake data with the following schema:
{get_database_schema()}

You have several tools at your disposal:
1. `sync_realtime_earthquakes`: Pulls latest real-time GeoJSON from USGS and updates the database.
2. `query_earthquakes`: Filter earthquakes by magnitude, region/place, time window, and tsunami alert.
3. `get_seismic_statistics`: Computes catalog aggregations (mean magnitude, active zones, tsunami count, strongest event).
4. `get_tsunami_alerts`: Returns all events that triggered a tsunami advisory or warning.
5. `execute_safe_sql`: Execute read-only SELECT queries for complex aggregations, joins, or specific temporal breakdowns.

CRITICAL FORMATTING & STYLE INSTRUCTIONS:
- NEVER USE TRIPLE ASTERISKS (***). Do not output '***' under any circumstance.
- Deliver responses clean, highly organized, and structured with clear titles, section numbering, and neat bullet points (•).
- When asked about PREVENTION (qué hacer antes, durante o después, mochila de emergencia, simulacros, protocolos costeros de tsunami):
  Provide actionable, lifesaving recommendations based on international standards (USGS, FEMA, Cruz Roja, Protección Civil).
- When asked about SEISMOLOGICAL SCIENCE (qué es un sismo, por qué tiembla, placas tectónicas, fallas, ondas P y S, escalas de magnitud Mw vs intensidad Mercalli MMI, enjambres sísmicos, predicción):
  Provide authoritative, rigorous scientific explanations while remaining clear and easy to understand.
- When asked about real-time telemetry, data, or SQL:
  Query the database tools and present tables cleanly.
- Language: Spanish (or match user language).
"""


class SeismicAgent:
    """Conversational relational agent equipped with function calling and offline fallback reasoning."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.model = model or settings.OPENAI_MODEL
        self.has_llm = bool(self.api_key and not self.api_key.startswith("your_"))
        self.client = OpenAI(api_key=self.api_key) if self.has_llm else None

        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def reset_chat(self) -> None:
        """Reset conversational context."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_input: str, user_role: str = "viewer") -> str:
        """
        Process user query in natural language, invoke tools, and return formatted response.
        Ensures clean, ordered presentation without triple asterisks.
        Adapts context and capabilities based on user_role ('admin' vs 'viewer').
        """
        if not user_input.strip():
            return "Por favor ingresa una pregunta o instrucción sobre sismos o prevención."

        raw_response = ""
        if not self.has_llm:
            raw_response = self._offline_reasoning(user_input, user_role=user_role)
        else:
            try:
                raw_response = self._llm_function_calling_loop(user_input, user_role=user_role)
            except Exception as e:
                logger.warning(f"LLM interaction failed ({e}), falling back to deterministic agent reasoning.")
                raw_response = self._offline_reasoning(user_input, user_role=user_role)

        return sanitize_response(raw_response)

    def _llm_function_calling_loop(self, user_input: str, user_role: str = "viewer", max_turns: int = 5) -> str:
        """Execute multi-turn tool calling loop with OpenAI."""
        role_context = f"[Contexto de Sesión: Usuario autenticado con rol '{user_role.upper()}']"
        self.messages.append({"role": "user", "content": f"{role_context} {user_input}"})

        for _ in range(max_turns):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=OPENAI_TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )

            msg = response.choices[0].message
            tool_calls = msg.tool_calls

            if not tool_calls:
                # LLM finished reasoning and produced a textual answer
                content = msg.content or "No se pudo generar respuesta."
                self.messages.append({"role": "assistant", "content": content})
                return content

            # Append the assistant's message requesting tool execution
            self.messages.append(msg)

            # Execute each requested tool
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                func_args_str = tool_call.function.arguments or "{}"
                call_id = tool_call.id

                try:
                    args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    args = {}

                logger.info(f"Agent invoking tool '{func_name}' with args {args}")
                handler = TOOL_DISPATCHER.get(func_name)

                if handler:
                    tool_output = handler(**args)
                else:
                    tool_output = {"error": f"Tool '{func_name}' not found."}

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(tool_output, default=str),
                })

        return "Se superó el límite de llamadas a herramientas sin converger."

    def _offline_reasoning(self, query: str, user_role: str = "viewer") -> str:
        """
        Deterministic NLP router and executor when OpenAI API Key is not set or network fails.
        Provides robust, standalone agent functionality without breaking the application.
        """
        # 1. Educational Seismology, Prevention & Admin Knowledge Base
        knowledge_ans = query_seismic_knowledge(query, user_role=user_role)
        if knowledge_ans:
            return knowledge_ans

        q = query.lower().strip()

        # 2. Direct SQL Query intent (Takes precedence if user enters SQL directly)
        if q.startswith("select ") or q.startswith("with "):
            res = execute_safe_sql(query)
            if res.get("status") == "error":
                return f"❌ {res.get('message')}"
            
            cols = res.get("columns", [])
            data = res.get("data", [])
            if not data:
                return f"ℹ️ La consulta retornó 0 filas.\n`{res.get('executed_query')}`"
            
            # Format markdown table
            header = "| " + " | ".join(cols) + " |"
            sep = "| " + " | ".join(["---"] * len(cols)) + " |"
            rows = []
            for d in data[:15]:
                row = "| " + " | ".join(str(d.get(c, "")) for c in cols) + " |"
                rows.append(row)
            
            table = "\n".join([header, sep] + rows)
            return (
                f"🔍 **Resultado de consulta SQL** ({res.get('row_count')} filas):\n\n"
                f"{table}\n\n"
                f"*Query ejecutado:* `{res.get('executed_query')}`"
            )

        # 3. Synchronization intent
        if any(w in q for w in ["sincroniza", "actualiza", "sync", "descarga", "ingesta", "recargar"]):
            res = sync_realtime_earthquakes()
            if res.get("status") == "success":
                return (
                    f"🔄 **Sincronización Completada con Éxito**\n\n"
                    f"• Fuente: `{res.get('feed_title')}`\n"
                    f"• Total de eventos leídos: {res.get('total_fetched')}\n"
                    f"• Nuevos sismos insertados: {res.get('new_inserted')}\n"
                    f"• Sismos actualizados: {res.get('existing_updated')}\n"
                    f"• Marca de tiempo USGS: {res.get('timestamp')}\n\n"
                    f"La base de datos relacional se encuentra al día con la última telemetría del USGS."
                )
            return f"❌ Error en la sincronización: {res.get('message')}"

        # 4. Tsunami alerts intent
        if any(w in q for w in ["tsunami", "alerta de tsunami", "costero", "tsunamis"]):
            res = get_tsunami_alerts()
            count = res.get("count", 0)
            if count == 0:
                return (
                    f"🌊 **Monitoreo de Tsunamis Activo**\n\n"
                    f"No se registran eventos con alerta de tsunami en la ventana de datos actual. "
                    f"Todos los eventos catalogados reportan tsunami = 0."
                )
            
            lines = [f"🚨 **Se detectaron {count} evento(s) con alerta o protocolo de tsunami:**\n"]
            for ev in res.get("events", []):
                lines.append(
                    f"• M {ev.get('magnitude')} en {ev.get('place')} "
                    f"| Prof: {ev.get('depth_km')} km | Fecha: `{ev.get('time')}` | [Detalles USGS]({ev.get('url')})"
                )
            return "\n".join(lines)

        # 5. Overall Statistics / Report intent
        if any(w in q for w in [
            "estadística", "estadistica", "resumen", "promedio", "general",
            "balance", "stats", "más activo", "mas activo", "zona", "zonas",
            "actividad", "sismicidad", "más fuerte", "mas fuerte"
        ]):
            stats = get_seismic_statistics()
            if stats.get("total_events", 0) == 0:
                return "ℹ️ La base de datos relacional está vacía. Ejecuta `sync` o solicita 'sincronizar datos'."

            strongest = stats.get("strongest_event") or {}
            regions_str = "\n".join(
                [f"  • {r['region']}: {r['event_count']} sismos (Mag máx: {r['max_magnitude']})"
                 for r in stats.get("top_active_regions", [])]
            )

            return (
                f"📊 **Reporte Estadístico de Actividad Sísmica**\n\n"
                f"• Total de sismos registrados: {stats.get('total_events')}\n"
                f"• Magnitud promedio: {stats.get('average_magnitude')}\n"
                f"• Rango de magnitud: Min {stats.get('min_magnitude')} | Max {stats.get('max_magnitude')}\n"
                f"• Profundidad promedio: {stats.get('average_depth_km')} km\n"
                f"• Alertas de tsunami activas: {stats.get('tsunami_warning_events')}\n"
                f"• Evento de mayor magnitud: M {strongest.get('magnitude')} en {strongest.get('place')} ({strongest.get('time')})\n\n"
                f"📍 **Zonas con mayor actividad:**\n{regions_str}"
            )

        # 6. Magnitude or geographic filter extraction
        min_mag = None
        mag_match = re.search(r"(?:mayor(?:es)?\s+a|magnitud\s*(?:>=?|>)\s*|mag\s*(?:>=?|>)\s*)(\d+(?:\.\d+)?)", q)
        if mag_match:
            min_mag = float(mag_match.group(1))

        # Look for regions
        place_filter = None
        for candidate in ["california", "alaska", "hawaii", "chile", "japan", "japon", "panama", "mexico", "puerto rico"]:
            if candidate in q:
                place_filter = candidate
                break

        if min_mag is not None or place_filter is not None or "sismos" in q or "terremoto" in q:
            results = query_earthquakes(
                min_magnitude=min_mag,
                place=place_filter,
                limit=15,
            )
            count = results.get("count", 0)
            if count == 0:
                return f"ℹ️ No se encontraron eventos sísmicos con los criterios seleccionados (Mag >= {min_mag}, Lugar: {place_filter})."

            lines = [f"🔎 **Se encontraron {count} sismos relevantes:**\n"]
            for ev in results.get("events", [])[:10]:
                lines.append(
                    f"• M {ev.get('magnitude')} ({ev.get('mag_type') or 'mag'}) - {ev.get('place')}\n"
                    f"  Prof: {ev.get('depth_km')} km | Tsunami: {'🚨 SÍ' if ev.get('tsunami_alert') else 'No'} | "
                    f"Hora: `{ev.get('time')}` | [USGS Link]({ev.get('url')})"
                )
            return "\n".join(lines)

        # Fallback helpful response (tailored by role)
        if user_role == "admin":
            return (
                "🤖 SeismoAgent (Modo Administrador) a tu disposición. Puedo ayudarte con:\n\n"
                "1. Gestión de Administración: '¿Qué veo en mi vista?', '¿Qué acciones puedo hacer como admin?', '¿Cómo hacer un backfill histórico?', '¿Por qué entran sismos en cuarentena?'.\n"
                "2. Orquestación y SLAs: 'Estado de DAGs en Airflow', 'Credenciales de Airflow (puerto 8080)', 'Regenerar reporte diario con IA'.\n"
                "3. Prevención Sísmica: '¿Qué hacer durante un sismo?', 'Mochila de emergencia de las 72 horas', 'Protocolo de tsunami'.\n"
                "4. Ciencia y Conceptos: '¿Qué es un sismo?', 'Ondas P y S', 'Diferencia entre Richter y Mercalli'.\n"
                "5. Telemetría y Datos: 'Sincronizar últimos sismos', 'Estadísticas generales', 'Sismos con magnitud > 2.5'.\n"
                "6. Consultas SQL Seguras: 'SELECT * FROM earthquakes ORDER BY magnitude DESC LIMIT 5'."
            )

        return (
            "🤖 SeismoAgent a tu disposición. Puedo ayudarte con:\n\n"
            "1. Prevención Sísmica: '¿Qué hacer antes, durante o después de un sismo?', 'Mochila de emergencia de las 72 horas', 'Protocolo de tsunami'.\n"
            "2. Ciencia y Conceptos: '¿Qué es un sismo?', '¿Por qué tiembla?', 'Ondas P y S', 'Diferencia entre Richter y Mercalli', 'Cinturón de Fuego'.\n"
            "3. Telemetría en Tiempo Real: 'Sincronizar últimos sismos', 'Estadísticas generales', '¿Hay alertas de tsunami?'.\n"
            "4. Filtros Sísmicos: 'Sismos con magnitud mayor a 2.5', 'Eventos en California o Alaska'.\n"
            "5. Consultas SQL Seguras: 'SELECT magnitude, place_name, time FROM earthquakes ORDER BY magnitude DESC LIMIT 5'."
        )
