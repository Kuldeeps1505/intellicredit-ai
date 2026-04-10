import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { AgentStatus, LogEntry } from "@/lib/agentData";
import { api, createPipelineWebSocket, LogEntryOut, AgentStateOut, ApplicationSummary } from "@/lib/api";

export type PipelineStatus = "idle" | "running" | "completed" | "error";

type NodeStatus = Record<string, { status: AgentStatus; elapsed: number }>;

interface UploadedFile {
  file: File;
  docType: string;
}

interface PipelineContextValue {
  // Active application (real data — no demo)
  applicationId: string | null;
  setApplicationId: (id: string | null) => void;
  application: ApplicationSummary | null;

  // Pipeline state
  pipelineStatus: PipelineStatus;
  running: boolean;
  finished: boolean;
  nodeStates: NodeStatus;
  visibleLogs: LogEntry[];
  overallProgress: number;
  riskToasts: LogEntry[];

  // Pending uploads
  pendingFiles: UploadedFile[];
  setPendingFiles: (files: UploadedFile[]) => void;

  // Controls
  startPipeline: (appId?: string) => Promise<void>;
  resetPipeline: () => void;
  setPipelineStatus: (s: PipelineStatus) => void;
}

const PipelineContext = createContext<PipelineContextValue | null>(null);

const STATUS_MAP: Record<string, AgentStatus> = {
  idle: "idle", running: "running", complete: "complete",
  STARTED: "running", RUNNING: "running", COMPLETED: "complete", ERROR: "error",
};

const POLL_MS = 2000;

export const PipelineProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [applicationId, setApplicationIdState] = useState<string | null>(null);
  const [application, setApplication] = useState<ApplicationSummary | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>("idle");
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState(false);
  const [nodeStates, setNodeStates] = useState<NodeStatus>({});
  const [visibleLogs, setVisibleLogs] = useState<LogEntry[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [riskToasts, setRiskToasts] = useState<LogEntry[]>([]);
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seenLogsRef = useRef<Set<string>>(new Set());

  const setApplicationId = useCallback((id: string | null) => {
    setApplicationIdState(id);
    if (id) {
      api.getApplication(id).then(setApplication).catch(() => {});
    } else {
      setApplication(null);
    }
  }, []);

  const resetPipeline = useCallback(() => {
    setRunning(false);
    setFinished(false);
    setNodeStates({});
    setVisibleLogs([]);
    setOverallProgress(0);
    setRiskToasts([]);
    setPipelineStatus("idle");
    seenLogsRef.current = new Set();
    wsRef.current?.close();
    wsRef.current = null;
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = null;
  }, []);

  const applyStatusResponse = useCallback((data: { agents: AgentStateOut[]; progress: number; logs: LogEntryOut[] }) => {
    const ns: NodeStatus = {};
    data.agents.forEach((a) => { ns[a.id] = { status: STATUS_MAP[a.status] ?? "idle", elapsed: a.duration }; });
    setNodeStates(ns);
    setOverallProgress(data.progress);

    const newLogs: LogEntry[] = data.logs.map((l) => ({
      timestamp: l.timestamp, agent: l.agent, message: l.message, level: l.level as LogEntry["level"],
    }));
    setVisibleLogs(newLogs);

    const fresh = newLogs.filter((l) => {
      const key = l.timestamp + l.message;
      if (seenLogsRef.current.has(key)) return false;
      seenLogsRef.current.add(key);
      return l.level === "critical";
    });
    if (fresh.length) setRiskToasts((prev) => [...prev, ...fresh].slice(-3));

    if (data.progress >= 100) {
      setRunning(false);
      setFinished(true);
      setPipelineStatus("completed");
      if (pollRef.current) clearInterval(pollRef.current);
      wsRef.current?.close();
    }
  }, []);

  const applyWsEvent = useCallback((event: Record<string, unknown>) => {
    const type = event.event_type as string;
    if (type === "AGENT_STATUS" || type === "agent_status") {
      const agentId = (event.agentId || event.agent_id) as string;
      const status = STATUS_MAP[(event.status as string) ?? "idle"] ?? "idle";
      if (agentId) setNodeStates((prev) => ({ ...prev, [agentId]: { status, elapsed: (event.elapsed as number) ?? 0 } }));
    }
    if (type === "AGENT_COMPLETE" || type === "agent_complete") {
      const agentId = (event.agentId || event.agent_id) as string;
      if (agentId) setNodeStates((prev) => ({ ...prev, [agentId]: { status: "complete", elapsed: (event.elapsed as number) ?? 0 } }));
      setOverallProgress((prev) => Math.min(prev + 11, 99));
    }
    if (type === "AGENT_ERROR" || type === "agent_error") {
      const agentId = (event.agentId || event.agent_id) as string;
      if (agentId) setNodeStates((prev) => ({ ...prev, [agentId]: { status: "error", elapsed: 0 } }));
    }
    if (type === "log" || type === "LOG") {
      const payload = (event.payload as Record<string, unknown>) ?? event;
      const entry: LogEntry = {
        timestamp: (event.timestamp as string ?? "").slice(11, 19) || "00:00:00",
        agent: (payload.agent_name || event.agent_name || "System") as string,
        message: (payload.message || payload.msg || JSON.stringify(payload)) as string,
        level: (payload.level as LogEntry["level"]) ?? "info",
      };
      const key = entry.timestamp + entry.message;
      if (!seenLogsRef.current.has(key)) {
        seenLogsRef.current.add(key);
        setVisibleLogs((prev) => [...prev, entry]);
        if (entry.level === "critical") setRiskToasts((prev) => [...prev, entry].slice(-3));
      }
    }
    if (type === "complete" || type === "COMPLETE" || type === "pipeline_complete") {
      setRunning(false); setFinished(true); setOverallProgress(100);
      setPipelineStatus("completed");
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, []);

  const startPolling = useCallback((appId: string) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try { const data = await api.getPipelineStatus(appId); applyStatusResponse(data); } catch { /* ignore */ }
    }, POLL_MS);
  }, [applyStatusResponse]);

  const connectWebSocket = useCallback((appId: string) => {
    try {
      wsRef.current?.close();
      const ws = createPipelineWebSocket(appId);
      wsRef.current = ws;
      ws.onmessage = (e) => { try { applyWsEvent(JSON.parse(e.data)); } catch { /* ignore */ } };
      ws.onerror = () => { wsRef.current = null; };
      ws.onclose = () => { wsRef.current = null; };
    } catch { /* WS unavailable — polling handles everything */ }
  }, [applyWsEvent]);

  const startPipeline = useCallback(async (appId?: string) => {
    const id = appId ?? applicationId;
    if (!id) { console.error("startPipeline: no applicationId"); return; }
    resetPipeline();
    setRunning(true);
    setPipelineStatus("running");
    try {
      await api.startPipeline(id);
    } catch (err) {
      console.error("Failed to start pipeline:", err);
      setPipelineStatus("error");
      setRunning(false);
      return;
    }
    startPolling(id);
    connectWebSocket(id);
  }, [applicationId, resetPipeline, connectWebSocket, startPolling]);

  useEffect(() => {
    return () => { wsRef.current?.close(); if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  return (
    <PipelineContext.Provider value={{
      applicationId, setApplicationId, application,
      pipelineStatus, setPipelineStatus, running, finished,
      nodeStates, visibleLogs, overallProgress, riskToasts,
      pendingFiles, setPendingFiles, startPipeline, resetPipeline,
    }}>
      {children}
    </PipelineContext.Provider>
  );
};

export const usePipeline = () => {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipeline must be used within PipelineProvider");
  return ctx;
};
