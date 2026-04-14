"""LangGraph DAG — Final (Day 4). All 7 agents + 2 engines + counterfactual."""
from __future__ import annotations
import asyncio, time
from datetime import datetime
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.services.redis_service import publish_event
from app.services.db_helper import log_agent, update_app_status

class PipelineState(TypedDict):
    app_id: str
    extracted_financials: Optional[dict]
    ratios: Optional[dict]
    anomaly_flags: Optional[list]
    research_dossier: Optional[dict]
    gst_reconciliation: Optional[dict]
    buyer_concentration: Optional[dict]
    risk_scores: Optional[dict]
    dd_adjustments: Optional[dict]
    decision: Optional[dict]
    counterfactuals: Optional[dict]
    cam_path: Optional[dict]
    errors: list

async def _err(app_id, name, e, t):
    dur=int((time.time()-t)*1000)
    await publish_event(app_id,{"event_type":"AGENT_ERROR","agent_name":name,"payload":{"error":str(e)},"timestamp":datetime.utcnow().isoformat()})
    await log_agent(app_id,name,"ERROR",error_message=str(e),duration_ms=dur)

async def node_document_intelligence(state):
    app_id=state["app_id"]; t=time.time()
    try:
        from agents.document_intelligence import run
        state["extracted_financials"]=await run(app_id)
    except Exception as e:
        state["errors"].append(f"doc_intel:{e}"); await _err(app_id,"document_intelligence",e,t)
    return state

async def node_parallel_analysis(state):
    app_id=state["app_id"]; extracted=state.get("extracted_financials") or {}
    async def r_fin():
        try:
            from agents.financial_analysis import run; return await run(app_id,extracted)
        except Exception as e: await _err(app_id,"financial_analysis",e,time.time()); return {}
    async def r_res():
        try:
            from agents.research_intelligence import run; return await run(app_id)
        except Exception as e: await _err(app_id,"research_intelligence",e,time.time()); return {}
    async def r_gst():
        try:
            from engines.gst_reconciliation import run; return await run(app_id)
        except Exception as e: await _err(app_id,"gst_reconciliation_engine",e,time.time()); return {}
    async def r_buy():
        try:
            from engines.buyer_concentration import run; return await run(app_id)
        except Exception as e: await _err(app_id,"buyer_concentration_engine",e,time.time()); return {}
    fr,rr,gr,br=await asyncio.gather(r_fin(),r_res(),r_gst(),r_buy())
    state["ratios"]=fr.get("ratios",{}); state["anomaly_flags"]=fr.get("anomaly_flags",[])
    state["research_dossier"]=rr; state["gst_reconciliation"]=gr; state["buyer_concentration"]=br
    return state

async def node_risk_assessment(state):
    app_id=state["app_id"]; t=time.time()
    try:
        from agents.risk_assessment import run; state["risk_scores"]=await run(app_id)
    except Exception as e:
        state["errors"].append(f"risk:{e}"); await _err(app_id,"risk_assessment",e,t)
    return state

async def node_credit_decision(state):
    app_id=state["app_id"]; t=time.time()
    try:
        from agents.credit_decision import run; state["decision"]=await run(app_id)
    except Exception as e:
        state["errors"].append(f"credit_decision:{e}"); await _err(app_id,"credit_decision",e,t)
    return state

async def node_counterfactual(state):
    app_id=state["app_id"]; t=time.time()
    try:
        from engines.counterfactual import run; state["counterfactuals"]=await run(app_id)
    except Exception as e:
        state["errors"].append(f"counterfactual:{e}"); await _err(app_id,"counterfactual_engine",e,t)
    return state

async def node_cam_generation(state):
    app_id=state["app_id"]; t=time.time()
    try:
        from agents.cam_generation import run; state["cam_path"]=await run(app_id)
    except Exception as e:
        state["errors"].append(f"cam:{e}"); await _err(app_id,"cam_generation",e,t)
    return state

def build_dag():
    g=StateGraph(PipelineState)
    g.add_node("document_intelligence",node_document_intelligence)
    g.add_node("parallel_analysis",node_parallel_analysis)
    g.add_node("risk_assessment",node_risk_assessment)
    g.add_node("credit_decision",node_credit_decision)
    g.add_node("counterfactual_engine",node_counterfactual)
    g.add_node("cam_generation",node_cam_generation)
    g.set_entry_point("document_intelligence")
    g.add_edge("document_intelligence","parallel_analysis")
    g.add_edge("parallel_analysis","risk_assessment")
    g.add_edge("risk_assessment","credit_decision")
    g.add_edge("credit_decision","counterfactual_engine")
    g.add_edge("counterfactual_engine","cam_generation")
    g.add_edge("cam_generation",END)
    return g.compile()

async def run_pipeline(app_id: str):
    pipeline=build_dag()
    initial: PipelineState={"app_id":app_id,"extracted_financials":None,"ratios":None,"anomaly_flags":None,"research_dossier":None,"gst_reconciliation":None,"buyer_concentration":None,"risk_scores":None,"dd_adjustments":None,"decision":None,"counterfactuals":None,"cam_path":None,"errors":[]}
    await update_app_status(app_id,"PROCESSING")
    try:
        final=await pipeline.ainvoke(initial)
        status="ERROR" if final.get("errors") else "COMPLETED"
    except Exception as e:
        status="ERROR"; final={**initial,"errors":[str(e)]}
    await update_app_status(app_id,status)
    return final
