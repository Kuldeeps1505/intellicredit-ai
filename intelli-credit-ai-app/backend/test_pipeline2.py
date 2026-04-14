"""Debug which stage hangs."""
import asyncio, sys, time
sys.path.insert(0, ".")

async def main():
    app_id = "99c0fad8-ac89-4dd9-a267-0744ee0ce4c3"

    print("Testing doc_intel...")
    t = time.time()
    try:
        from agents.document_intelligence import run as doc_run
        result = await asyncio.wait_for(doc_run(app_id), timeout=15)
        print(f"doc_intel OK in {time.time()-t:.1f}s: {len(result)} fields")
    except asyncio.TimeoutError:
        print(f"doc_intel TIMEOUT after {time.time()-t:.1f}s")
    except Exception as e:
        print(f"doc_intel ERROR: {e}")

    print("Testing financial_analysis...")
    t = time.time()
    try:
        from agents.financial_analysis import run as fin_run
        result = await asyncio.wait_for(fin_run(app_id, {}), timeout=15)
        print(f"fin_analysis OK in {time.time()-t:.1f}s")
    except asyncio.TimeoutError:
        print(f"fin_analysis TIMEOUT after {time.time()-t:.1f}s")
    except Exception as e:
        print(f"fin_analysis ERROR: {e}")

    print("Testing risk_assessment...")
    t = time.time()
    try:
        from agents.risk_assessment import run as risk_run
        result = await asyncio.wait_for(risk_run(app_id), timeout=30)
        print(f"risk_assessment OK in {time.time()-t:.1f}s")
    except asyncio.TimeoutError:
        print(f"risk_assessment TIMEOUT after {time.time()-t:.1f}s")
    except Exception as e:
        print(f"risk_assessment ERROR: {e}")

asyncio.run(main())
