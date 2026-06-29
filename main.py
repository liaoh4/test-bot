import argparse
import asyncio
import sys

import httpx
import uvicorn
from pyngrok import ngrok

from caller_bot import app, bot
from config import settings
from reporter import generate_report
from scenarios import ALL_SCENARIOS, Scenario


async def reset_and_seed() -> str:
    if not settings.BACKEND_URL or not settings.TEST_RESET_SECRET:
        return ""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.BACKEND_URL}/api/test-reset",
            json={"caller_phone": settings.TWILIO_CALLER_NUMBER, "target_phone": settings.TARGET_PHONE_NUMBER},
            headers={"x-reset-secret": settings.TEST_RESET_SECRET},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[reset] deleted {data['deleted_clients']} clients, blocker date: {data['blocked_date']}")
        return data["blocked_date"]


async def run_scenarios(selected: list[Scenario], blocked_date: str = ""):
    results = []
    for scenario in selected:
        print(f"\n[{scenario.id}] Starting: {scenario.name}")
        try:
            result = await bot.run_scenario(
                scenario,
                patient_name=settings.PATIENT_NAME,
                patient_dob=settings.PATIENT_DOB,
                blocked_date=blocked_date,
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

    blocked_date = await reset_and_seed()
    results = await run_scenarios(selected, blocked_date=blocked_date)

    server.should_exit = True
    await server_task

    if results:
        report_path = generate_report(results)
        print(f"\nBug report: {report_path}")
    else:
        print("\nNo results to report.")


if __name__ == "__main__":
    asyncio.run(main())
