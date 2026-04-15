"""Run _trigger_pipeline directly to see the actual error."""
import asyncio, sys
sys.path.insert(0, ".")

async def main():
    app_id = "d67f8ec8-a130-4dda-957e-820fd21f9c66"
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
