#!/usr/bin/env python3
"""
CLI and Interactive Entrypoint for the Seismic Monitoring Relational Agent.
"""

import argparse
import sys
from pathlib import Path

# Ensure parent directory is in sys.path so 'import agentebot' works regardless of execution directory
CURRENT_FILE = Path(__file__).resolve()
PARENT_DIR = CURRENT_FILE.parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from agentebot.config import settings
from agentebot.database.connection import init_db
from agentebot.agent.core import SeismicAgent
from agentebot.agent.tools import (
    sync_realtime_earthquakes,
    get_seismic_statistics,
    get_tsunami_alerts,
    get_database_schema,
    execute_safe_sql,
)

BANNER = r"""
╔════════════════════════════════════════════════════════════════════╗
║                🌍 SEISMOWATCH RELATIONAL AGENT 🌍                  ║
║         Monitoreo Sísmico & Análisis Relacional en Tiempo Real     ║
╚════════════════════════════════════════════════════════════════════╝
"""


def print_help() -> None:
    print("""
Comandos interactivos disponibles:
  sync                 - Sincroniza la BD con la última telemetría del USGS.
  stats                - Muestra estadísticas agregadas y zonas más activas.
  tsunami              - Consulta alertas y avisos de tsunami activos.
  schema               - Muestra el esquema de las tablas relacionales.
  sql <consulta>       - Ejecuta una consulta SQL SELECT directa y segura.
  reset                - Reinicia el contexto de la conversación.
  help                 - Muestra este menú de ayuda.
  exit / quit          - Salir del agente.

También puedes escribir cualquier pregunta en lenguaje natural, por ejemplo:
  • "¿Cuáles fueron los 3 sismos más fuertes de la última hora?"
  • "¿Qué zonas presentan mayor sismicidad?"
  • "¿Hay algún sismo con magnitud superior a 4.0?"
""")


def run_interactive_loop(agent: SeismicAgent) -> None:
    """Run interactive REPL loop."""
    print(BANNER)
    llm_status = f"OpenAI ({agent.model})" if agent.has_llm else "Motor NLP Local (Reglas & Dispatcher Relacional)"
    print(f"🔹 Base de datos: {settings.resolved_database_url}")
    print(f"🔹 Proveedor IA:  {llm_status}")
    print(f"🔹 Feed USGS:     {settings.USGS_FEED_URL}")
    print("\nEscribe tu pregunta o 'help' para ver los comandos. Escribe 'exit' para salir.\n")

    while True:
        try:
            user_input = input("\033[1;36mSeismoAgent>\033[0m ").strip()
            if not user_input:
                continue

            cmd_lower = user_input.lower()

            if cmd_lower in ("exit", "quit", "q"):
                print("\n👋 Finalizando sesión con SeismoAgent. ¡Hasta luego!")
                break

            if cmd_lower in ("help", "?"):
                print_help()
                continue

            if cmd_lower == "sync":
                res = sync_realtime_earthquakes()
                print(f"\n🔄 {res.get('message')} | Insertados: {res.get('new_inserted')} | Actualizados: {res.get('existing_updated')}\n")
                continue

            if cmd_lower == "stats":
                stats = get_seismic_statistics()
                print("\n📊 Estadísticas Sísmicas:")
                for k, v in stats.items():
                    print(f"  • {k}: {v}")
                print()
                continue

            if cmd_lower == "tsunami":
                alerts = get_tsunami_alerts()
                print(f"\n🌊 Alertas de Tsunami ({alerts.get('count')} evento(s)):")
                for ev in alerts.get("events", []):
                    print(f"  • M {ev['magnitude']} - {ev['place']} ({ev['time']})")
                print()
                continue

            if cmd_lower == "schema":
                print("\n📐 Esquema de la Base de Datos Relacional:")
                print(get_database_schema())
                continue

            if cmd_lower.startswith("sql "):
                query = user_input[4:].strip()
                res = execute_safe_sql(query)
                if res.get("status") == "error":
                    print(f"\n❌ {res.get('message')}\n")
                else:
                    cols = res.get("columns", [])
                    data = res.get("data", [])
                    print(f"\n🔍 Filas retornadas: {res.get('row_count')}")
                    if data:
                        header = " | ".join(cols)
                        print(header)
                        print("-" * len(header))
                        for row in data[:20]:
                            print(" | ".join(str(row.get(c, "")) for c in cols))
                    print()
                continue

            if cmd_lower == "reset":
                agent.reset_chat()
                print("🔄 Contexto conversacional reiniciado.")
                continue

            # Process prompt with agent
            print("\n\033[1;33mPensando y consultando telemetría...\033[0m\n")
            response = agent.chat(user_input)
            print(f"{response}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n\nSesión interrumpida. Saliendo...")
            break
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}\n")


def main() -> None:
    """Entry point parsing command-line flags."""
    parser = argparse.ArgumentParser(
        description="Agente Relacional para Monitoreo y Análisis Sísmico (USGS)"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sincronizar base de datos con USGS y salir.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostrar estadísticas agregadas del catálogo y salir.",
    )
    parser.add_argument(
        "--tsunami",
        action="store_true",
        help="Consultar alertas de tsunami activas y salir.",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Ejecutar una consulta en lenguaje natural o SQL y salir.",
    )
    parser.add_argument(
        "--feed",
        type=str,
        help="URL alternativa del feed GeoJSON de USGS.",
    )

    args = parser.parse_args()

    # Ensure tables exist
    init_db()

    # Initialize agent
    agent = SeismicAgent()

    if args.sync:
        print("Sincronizando telemetría USGS...")
        res = sync_realtime_earthquakes(feed_url=args.feed)
        print(f"Resultado: {res.get('message')}")
        print(f"Total eventos: {res.get('total_fetched')} | Insertados: {res.get('new_inserted')} | Actualizados: {res.get('existing_updated')}")
        sys.exit(0)

    if args.stats:
        stats = get_seismic_statistics()
        print("\nEstadísticas Sísmicas Actuales:")
        for k, v in stats.items():
            print(f"  • {k}: {v}")
        sys.exit(0)

    if args.tsunami:
        alerts = get_tsunami_alerts()
        print(f"\nAlertas de Tsunami: {alerts.get('count')} evento(s) detectados.")
        for ev in alerts.get("events", []):
            print(f"  • M {ev['magnitude']} - {ev['place']} ({ev['time']})")
        sys.exit(0)

    if args.query:
        answer = agent.chat(args.query)
        print(answer)
        sys.exit(0)

    # Interactive mode by default
    run_interactive_loop(agent)


if __name__ == "__main__":
    main()
