"""Run _trigger_pipeline directly to see the actual error."""
import asyncio, sys
sys.path.insert(0, ".")

async def main():
    app_id = "8609cade-0dd8-495b-8772-8b97c5cd8a77"
    print(f"Testing pipeline for app: {app_id}")
    try:
        from app.routers.applications import _trigger_pipeline
        await _trigger_pipeline(app_id)
        print("Pipeline completed OK")
    except Exception as e:
        import traceback
        print("PIPELINE CRASHED:")
        traceback.print_exc()

asyncio.run(main())
