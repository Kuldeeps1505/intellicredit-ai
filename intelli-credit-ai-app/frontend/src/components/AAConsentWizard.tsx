/**
 * Account Aggregator Consent Wizard — India Stack
 * Real 3-step flow: Initiate → Borrower Approves → Fetch FI Data
 * Uses actual AA APIs (Setu/Sahamati sandbox) with mock fallback.
 */
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Phone, Smartphone, FileText, Check, CheckCircle2, Loader2, AlertCircle, ExternalLink, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

type AAStep = "idle" | "initiating" | "consent_pending" | "consent_active" | "fetching" | "done" | "error";

interface Props {
  applicationId: string | null;
  onDataFetched?: () => void;
}

export function AAConsentWizard({ applicationId, onDataFetched }: Props) {
  const [step, setStep] = useState<AAStep>("idle");
  const [mobile, setMobile] = useState("+91 ");
  const [consentHandle, setConsentHandle] = useState("");
  const [redirectUrl, setRedirectUrl] = useState("");
  const [provider, setProvider] = useState("mock");
  const [aaApp, setAaApp] = useState("OneMoney / Finvu");
  const [error, setError] = useState("");
  const [fetchResult, setFetchResult] = useState<any>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll consent status when pending
  useEffect(() => {
    if (step !== "consent_pending" || !applicationId) return;
    pollRef.current = setInterval(async () => {
      try {
        const status = await api.aaConsentStatus(applicationId);
        if (status.status === "ACTIVE") {
          clearInterval(pollRef.current!);
          setStep("consent_active");
        } else if (status.status === "REJECTED" || status.status === "EXPIRED") {
          clearInterval(pollRef.current!);
          setError(`Consent ${status.status.toLowerCase()} by borrower.`);
          setStep("error");
        }
      } catch { /* ignore */ }
    }, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [step, applicationId]);

  const handleInitiate = async () => {
    if (!applicationId) { setError("Create application first."); return; }
    const mobileClean = mobile.replace(/\s/g, "").replace("+91", "");
    if (mobileClean.length !== 10) { setError("Enter valid 10-digit mobile number."); return; }
    setError("");
    setStep("initiating");
    try {
      const result = await api.aaInitiateConsent(applicationId, mobile.trim());
      setConsentHandle(result.consentHandle);
      setRedirectUrl(result.redirectUrl);
      setProvider(result.provider);
      setAaApp(result.aaApp || "OneMoney / Finvu / CAMS Finserv");
      setStep("consent_pending");
    } catch (e: any) {
      setError(e.message || "Failed to initiate consent.");
      setStep("error");
    }
  };

  const handleFetchData = async () => {
    if (!applicationId) return;
    setStep("fetching");
    try {
      const result = await api.aaFetchFI(applicationId);
      setFetchResult(result);
      setStep("done");
      onDataFetched?.();
    } catch (e: any) {
      setError(e.message || "Failed to fetch financial data.");
      setStep("error");
    }
  };

  const stepNum = step === "idle" ? 0
    : step === "initiating" || step === "consent_pending" ? 1
    : step === "consent_active" ? 2
    : step === "fetching" || step === "done" ? 3 : 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm text-primary">Account Aggregator Flow</h3>
        <div className="flex items-center gap-1.5">
          <Shield className="h-3 w-3 text-safe" />
          <span className="text-[10px] text-safe font-display">RBI Licensed · End-to-End Encrypted</span>
        </div>
      </div>

      {/* India Stack badge */}
      <div className="flex gap-2 flex-wrap">
        {["India Stack AA", "ReBIT 2.0", "Zero Manual Upload", "GSTN + Bank"].map(tag => (
          <Badge key={tag} className="text-[9px] bg-primary/10 text-primary border-primary/20 px-1.5 py-0">{tag}</Badge>
        ))}
      </div>

      {/* Steps */}
      <div className="space-y-0">
        {/* Step 1 */}
        <StepRow
          num={1} title="Enter Borrower Mobile" completed={stepNum > 1} active={stepNum === 1 || stepNum === 0}
        >
          <div className="mt-3 space-y-2">
            <div className="flex gap-2">
              <Input
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
                placeholder="+91 98765 43210"
                className="h-9 font-mono-numbers text-sm"
                disabled={step !== "idle" && step !== "error"}
              />
              <Button
                size="sm"
                onClick={handleInitiate}
                disabled={step !== "idle" && step !== "error"}
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-display text-xs shrink-0"
              >
                {step === "initiating" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Send Consent"}
              </Button>
            </div>
            <p className="text-[10px] text-muted-foreground">
              Borrower will receive a consent request on their AA app ({aaApp})
            </p>
          </div>
        </StepRow>

        {/* Step 2 */}
        <StepRow
          num={2} title="Borrower Approves on AA App" completed={stepNum > 2} active={stepNum === 2}
        >
          <AnimatePresence>
            {stepNum >= 2 && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-3 space-y-3">
                {step === "consent_pending" && (
                  <div className="flex items-center gap-3 p-3 bg-info/10 border border-info/20 rounded-lg">
                    <Loader2 className="h-4 w-4 text-info animate-spin shrink-0" />
                    <div>
                      <p className="text-xs font-display text-foreground">Waiting for borrower approval...</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        Borrower opens {aaApp} app → approves consent request
                      </p>
                    </div>
                  </div>
                )}
                {redirectUrl && (
                  <a
                    href={redirectUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-[10px] text-primary hover:underline"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Open AA consent page (for demo/testing)
                  </a>
                )}
                {step === "consent_active" && (
                  <div className="flex items-center gap-2 p-2.5 bg-safe/10 border border-safe/20 rounded-lg">
                    <CheckCircle2 className="h-4 w-4 text-safe shrink-0" />
                    <div>
                      <p className="text-xs font-display text-safe">Consent APPROVED ✓</p>
                      <p className="text-[10px] text-muted-foreground">
                        Handle: {consentHandle.slice(0, 20)}... · Provider: {provider}
                      </p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </StepRow>

        {/* Step 3 */}
        <StepRow
          num={3} title="Financial Data Fetched Automatically" completed={step === "done"} active={stepNum === 3}
          last
        >
          <AnimatePresence>
            {step === "consent_active" && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-3 space-y-3">
                <p className="text-[10px] text-muted-foreground">
                  Click to fetch bank statements (12 months) + GST returns automatically. No manual upload needed.
                </p>
                <Button
                  size="sm"
                  onClick={handleFetchData}
                  className="bg-safe text-white hover:bg-safe/90 font-display text-xs gap-1.5"
                >
                  <FileText className="h-3.5 w-3.5" />
                  Fetch Bank + GST Data via AA
                </Button>
              </motion.div>
            )}
            {step === "fetching" && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
                <span className="text-xs text-muted-foreground">Fetching from FIP (bank + GSTN)...</span>
              </motion.div>
            )}
            {step === "done" && fetchResult && (
              <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="mt-3 space-y-2">
                {[
                  { label: "Bank Statements (12M)", done: fetchResult.bankStatementsFetched },
                  { label: "GST Returns (GSTR-1, 2A, 3B)", done: fetchResult.gstDataFetched },
                  { label: "Account Summary", done: true },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2 text-sm font-body">
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                      <CheckCircle2 className="h-4 w-4 text-safe" />
                    </motion.div>
                    <span className="text-foreground">{item.label}</span>
                  </div>
                ))}
                <p className="text-[10px] text-safe font-display mt-2">
                  ✓ {fetchResult.message}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </StepRow>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-destructive text-xs bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          {error}
          <button onClick={() => { setStep("idle"); setError(""); }} className="ml-auto text-[10px] underline">
            Retry
          </button>
        </div>
      )}
    </div>
  );
}

function StepRow({
  num, title, completed, active, last = false, children
}: {
  num: number; title: string; completed: boolean; active: boolean; last?: boolean; children?: React.ReactNode;
}) {
  return (
    <div className="relative">
      {num > 1 && (
        <div className={`absolute left-[15px] -top-0 w-0.5 h-4 ${completed || active ? "bg-primary" : "bg-border"}`} />
      )}
      <div className={`relative pl-10 pb-5 ${!last ? "border-l-2 ml-[15px]" : "ml-[15px]"} ${completed ? "border-primary" : "border-border"}`}>
        <div className={`absolute left-[-13px] top-0 h-[26px] w-[26px] rounded-full flex items-center justify-center border-2 ${
          completed ? "bg-primary border-primary" : active ? "bg-card border-primary" : "bg-card border-border"
        }`}>
          {completed
            ? <Check className="h-3.5 w-3.5 text-primary-foreground" />
            : <span className={`text-[10px] font-display ${active ? "text-primary" : "text-muted-foreground"}`}>{num}</span>
          }
        </div>
        <h4 className={`text-sm font-display font-medium ${active || completed ? "text-foreground" : "text-muted-foreground"}`}>
          {title}
        </h4>
        {children}
      </div>
    </div>
  );
}
