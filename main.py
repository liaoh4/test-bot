import argparse
import asyncio
import sys

import uvicorn
from pyngrok import ngrok

from caller_bot import app, bot
from config import settings
from reporter import generate_report
from scenarios import ALL_SCENARIOS, Scenario


async def run_scenarios(selected: list[Scenario]):
    results = []
    for scenario in selected:
        print(f"\n[{scenario.id}] Starting: {scenario.name}")
        try:
            result = await bot.run_scenario(
                scenario,
                patient_name=settings.PATIENT_NAME,
                patient_dob=settings.PATIENT_DOB,
            )
            results.append(result)
            print(f"[{scenario.id}] Done — {len(result.turn_timestamps)} rounds")
        except asyncio.TimeoutError:
            print(f"[{scenario.id}] Timed out after {scenario.max_duration_sec}s")
        except Exception as e:
            print(f"[{scenario.id}] Failed: {e}")
    return results


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=str, default=None)
    args = parser.parse_args()

    selected = [s for s in ALL_SCENARIOS if args.scenario is None or s.id == args.scenario]
    if not selected:
        print(f"Unknown scenario: {args.scenario}")
        print("Available:", ", ".join(s.id for s in ALL_SCENARIOS))
        sys.exit(1)

    if settings.USE_NGROK:
        tunnel = ngrok.connect(settings.APP_PORT, "http")
        settings.WEBHOOK_BASE_URL = tunnel.public_url
        print(f"ngrok tunnel: {settings.WEBHOOK_BASE_URL}")

    config = uvicorn.Config(app, host="0.0.0.0", port=settings.APP_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())

    while not server.started:
        await asyncio.sleep(0.1)

    results = await run_scenarios(selected)

    server.should_exit = True
    await server_task

    if results:
        report_path = generate_report(results)
        print(f"\nBug report: {report_path}")
    else:
        print("\nNo results to report.")


if __name__ == "__main__":
    asyncio.run(main())
