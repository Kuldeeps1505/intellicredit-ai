import React, { useState, useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Link2, FileText, CheckCircle2, AlertCircle, Loader2, Rocket, Info, Phone, Smartphone, Check } from "lucide-react";
import { useDataset } from "@/contexts/DatasetContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type UploadMode = "manual" | "aa";

interface DocItem {
  name: string;
  status: "pending" | "uploading" | "extracted" | "error";
  size?: string;
}

const requiredDocs: DocItem[] = [
  { name: "Annual Report (3 years)", status: "pending" },
  { name: "Bank Statements (12 months)", status: "pending" },
  { name: "GST Returns (GSTR-1, 2A, 3B)", status: "pending" },
  { name: "Income Tax Returns (3 years)", status: "pending" },
  { name: "Audited Financials", status: "pending" },
  { name: "Memorandum of Association", status: "pending" },
];

const statusIcon = {
  pending: <div className="h-4 w-4 rounded border border-border" />,
  uploading: <Loader2 className="h-4 w-4 text-info animate-spin" />,
  extracted: <CheckCircle2 className="h-4 w-4 text-safe" />,
  error: <AlertCircle className="h-4 w-4 text-destructive" />,
};

export default function DocumentUpload() {
  const { dataset } = useDataset();
  const [mode, setMode] = useState<UploadMode>("manual");
  const [docs, setDocs] = useState<DocItem[]>(requiredDocs);
  const [aaStep, setAaStep] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [showDocPicker, setShowDocPicker] = useState(false);
  const [selectedDocIndex, setSelectedDocIndex] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formValues, setFormValues] = useState({
    companyName: dataset.companyName,
    cin: dataset.cin,
    pan: dataset.pan,
    gstin: dataset.gstin,
    loanAmount: dataset.loanAmount,
    purpose: dataset.purpose,
    sector: dataset.sector,
  });

  useEffect(() => {
    setFormValues({
      companyName: dataset.companyName,
      cin: dataset.cin,
      pan: dataset.pan,
      gstin: dataset.gstin,
      loanAmount: dataset.loanAmount,
      purpose: dataset.purpose,
      sector: dataset.sector,
    });
  }, [dataset]);

  const handleFieldChange = (field: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [field]: value }));
  };

  const simulateUploadForDoc = useCallback((index: number) => {
    setDocs((prev) =>
      prev.map((d, i) =>
        i === index
          ? { ...d, status: "uploading" }
          : d
      )
    );
    // Simulate extraction after a delay
    setTimeout(() => {
      setDocs((prev) =>
        prev.map((d, i) =>
          i === index
            ? { ...d, status: "extracted", size: `${(Math.random() * 4 + 1).toFixed(1)} MB` }
            : d
        )
      );
    }, 1500);
  }, []);

  const handleDropZoneClick = () => {
    setShowDocPicker(true);
  };

  const handleDocSelect = (index: number) => {
    setSelectedDocIndex(index);
    setShowDocPicker(false);
    // Trigger file input
    fileInputRef.current?.click();
  };

  const handleFileSelected = () => {
    if (selectedDocIndex !== null) {
      simulateUploadForDoc(selectedDocIndex);
      setSelectedDocIndex(null);
    }
    // Reset file input
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      setShowDocPicker(true);
    },
    []
  );

  const advanceAA = () => {
    if (aaStep < 3) setAaStep((s) => s + 1);
  };

  return (
    <div className="animate-slide-up">
      {/* Info Banner */}
      <div className="bg-secondary/50 border border-border rounded-lg px-4 py-2.5 mb-6 flex items-center gap-3">
        <Info className="h-4 w-4 text-primary shrink-0" />
        <p className="text-xs text-muted-foreground font-body">
          IntelliCredit AI is India Stack-native. AA-enabled borrowers need zero manual uploads.
        </p>
        <div className="ml-auto flex items-center gap-2 text-[10px] text-muted-foreground/60">
          <span>GSTN</span>
          <span>•</span>
          <span>AA</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* LEFT — Form (2/5) */}
        <div data-tour="upload-form" className="lg:col-span-2 space-y-6">
          <h2 className="font-display text-primary text-base font-semibold">
            New Credit Application
          </h2>

          <div className="space-y-4">
            {[
              { label: "Company Name", field: "companyName" },
              { label: "CIN", field: "cin" },
              { label: "PAN", field: "pan" },
              { label: "GSTIN", field: "gstin" },
            ].map((item) => (
              <div key={item.label} className="space-y-1">
                <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-display">
                  {item.label}
                </label>
                <Input
                  value={formValues[item.field as keyof typeof formValues]}
                  onChange={(e) => handleFieldChange(item.field, e.target.value)}
                  className="h-9 border-0 border-b border-border rounded-none bg-transparent px-0 text-sm font-body text-foreground focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-primary"
                />
              </div>
            ))}

            <div className="space-y-1">
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-display">
                Loan Amount
              </label>
              <div className="relative">
                <span className="absolute left-0 top-1/2 -translate-y-1/2 text-primary text-sm">₹</span>
                <Input
                  value={formValues.loanAmount}
                  onChange={(e) => handleFieldChange("loanAmount", e.target.value)}
                  className="h-9 border-0 border-b border-border rounded-none bg-transparent pl-4 pr-0 text-sm font-mono-numbers text-foreground focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-primary"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-display">
                  Purpose
                </label>
                <Input
                  value={formValues.purpose}
                  onChange={(e) => handleFieldChange("purpose", e.target.value)}
                  className="h-9 border-0 border-b border-border rounded-none bg-transparent px-0 text-sm font-body text-foreground focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-primary"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-display">
                  Sector
                </label>
                <Input
                  value={formValues.sector}
                  onChange={(e) => handleFieldChange("sector", e.target.value)}
                  className="h-9 border-0 border-b border-border rounded-none bg-transparent px-0 text-sm font-body text-foreground focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-primary"
                />
              </div>
            </div>
          </div>

          {/* AA Toggle */}
          <div data-tour="upload-source" className="pt-2">
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-display mb-2 block">
              Data Source
            </label>
            <div className="flex bg-secondary rounded-lg p-1">
              <button
                onClick={() => { setMode("manual"); setAaStep(0); }}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-display font-medium transition-all ${
                  mode === "manual"
                    ? "bg-card text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Upload className="h-3.5 w-3.5" />
                Manual Upload
              </button>
              <button
                onClick={() => setMode("aa")}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-md text-xs font-display font-medium transition-all ${
                  mode === "aa"
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Link2 className="h-3.5 w-3.5" />
                Account Aggregator
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT — Upload / AA (3/5) */}
        <div data-tour="upload-area" className="lg:col-span-3">
          <AnimatePresence mode="wait">
            {mode === "manual" ? (
              <motion.div
                key="manual"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                {/* Hidden file input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.xlsx,.csv,.xls"
                  className="hidden"
                  onChange={handleFileSelected}
                />

                {/* Drop Zone */}
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  onClick={handleDropZoneClick}
                  className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all ${
                    dragOver
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/40"
                  }`}
                >
                  <Upload className={`h-8 w-8 mx-auto mb-3 transition-colors ${dragOver ? "text-primary" : "text-muted-foreground"}`} />
                  <p className="text-sm font-body text-muted-foreground">
                    Drag & drop documents here or{" "}
                    <span className="text-primary underline">browse files</span>
                  </p>
                  <p className="text-[10px] text-muted-foreground/60 mt-1">
                    PDF, XLSX, CSV — up to 50MB per file
                  </p>
                </div>

                {/* Document Picker Modal */}
                <AnimatePresence>
                  {showDocPicker && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.15 }}
                      className="bg-card border border-border rounded-lg shadow-lg overflow-hidden"
                    >
                      <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
                        <h3 className="text-xs font-display text-primary uppercase tracking-wider">
                          Select Document to Upload
                        </h3>
                        <button
                          onClick={(e) => { e.stopPropagation(); setShowDocPicker(false); }}
                          className="text-muted-foreground hover:text-foreground text-xs"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="divide-y divide-border">
                        {docs.map((doc, idx) => (
                          <button
                            key={doc.name}
                            onClick={(e) => { e.stopPropagation(); handleDocSelect(idx); }}
                            disabled={doc.status === "extracted" || doc.status === "uploading"}
                            className={`w-full px-4 py-3 flex items-center gap-3 text-sm font-body text-left transition-colors ${
                              doc.status === "extracted"
                                ? "opacity-50 cursor-not-allowed bg-secondary/30"
                                : doc.status === "uploading"
                                ? "opacity-50 cursor-not-allowed"
                                : "hover:bg-secondary/50 cursor-pointer"
                            }`}
                          >
                            {statusIcon[doc.status]}
                            <span className={doc.status === "extracted" ? "text-muted-foreground line-through" : "text-foreground"}>
                              {doc.name}
                            </span>
                            {doc.status === "extracted" && (
                              <span className="ml-auto text-[10px] font-mono-numbers text-safe">Uploaded</span>
                            )}
                            {doc.status === "uploading" && (
                              <span className="ml-auto text-[10px] text-info">Uploading...</span>
                            )}
                            {doc.status === "pending" && (
                              <span className="ml-auto text-[10px] text-primary">Select</span>
                            )}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Document Checklist */}
                <div className="bg-card border border-border rounded-lg overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-border">
                    <h3 className="text-xs font-display text-muted-foreground uppercase tracking-wider">
                      Required Documents
                    </h3>
                  </div>
                  <div className="divide-y divide-border">
                    {docs.map((doc) => (
                      <div
                        key={doc.name}
                        className={`px-4 py-2.5 flex items-center gap-3 text-sm font-body transition-colors ${
                          doc.status === "extracted" ? "bg-safe/5" : ""
                        }`}
                      >
                        {statusIcon[doc.status]}
                        <span className={doc.status === "extracted" ? "text-foreground font-medium" : "text-muted-foreground"}>
                          {doc.name}
                        </span>
                        <div className="ml-auto flex items-center gap-2">
                          {doc.size && (
                            <span className="text-[10px] font-mono-numbers text-muted-foreground">
                              {doc.size}
                            </span>
                          )}
                          {doc.status === "extracted" && (
                            <span className="text-[10px] font-display text-safe font-medium">✓ Uploaded</span>
                          )}
                          {doc.status === "uploading" && (
                            <span className="text-[10px] font-display text-info">Uploading...</span>
                          )}
                          {doc.status === "pending" && (
                            <span className="text-[10px] font-display text-muted-foreground/50">Pending</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="aa"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="bg-card border border-border rounded-lg p-6"
              >
                <h3 className="font-display text-sm text-primary mb-6">
                  Account Aggregator Flow
                </h3>

                {/* AA Steps */}
                <div className="space-y-0">
                  {[
                    {
                      step: 1,
                      title: "Enter Borrower Mobile",
                      icon: Phone,
                      content: (
                        <div className="flex gap-2 mt-2">
                          <div className="flex-1 border-b border-border pb-2 text-sm font-mono-numbers text-foreground">
                            +91 98765 43210
                          </div>
                          <Button
                            size="sm"
                            onClick={advanceAA}
                            className="bg-primary text-primary-foreground hover:bg-primary/90 font-display text-xs"
                          >
                            Send OTP
                          </Button>
                        </div>
                      ),
                    },
                    {
                      step: 2,
                      title: "Borrower Approves on AA App",
                      icon: Smartphone,
                      content: (
                        <div className="mt-3 flex items-center gap-4">
                          <div className="w-20 h-36 bg-secondary rounded-xl border border-border flex items-center justify-center">
                            {aaStep >= 2 ? (
                              <Check className="h-8 w-8 text-safe" />
                            ) : (
                              <Loader2 className="h-5 w-5 text-info animate-spin" />
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {aaStep >= 2 ? "Consent approved ✓" : "Waiting for borrower to approve consent..."}
                          </p>
                        </div>
                      ),
                    },
                    {
                      step: 3,
                      title: "Data Fetched Automatically",
                      icon: FileText,
                      content: (
                        <div className="mt-2 space-y-1.5">
                          {["Bank Statements", "GST Returns", "ITR Data"].map((item, i) => (
                            <div key={item} className="flex items-center gap-2 text-sm font-body">
                              {aaStep >= 3 ? (
                                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: i * 0.2 }}>
                                  <CheckCircle2 className="h-4 w-4 text-safe" />
                                </motion.div>
                              ) : (
                                <div className="h-4 w-4 rounded-full border border-border" />
                              )}
                              <span className={aaStep >= 3 ? "text-foreground" : "text-muted-foreground"}>
                                {item}
                              </span>
                            </div>
                          ))}
                        </div>
                      ),
                    },
                  ].map((s, idx) => {
                    const completed = aaStep > idx;
                    const active = aaStep === idx;
                    return (
                      <div key={s.step} className="relative">
                        {/* Connector line */}
                        {idx > 0 && (
                          <div className={`absolute left-[15px] -top-0 w-0.5 h-4 ${completed ? "bg-primary" : "bg-border"}`} />
                        )}
                        <div
                          className={`relative pl-10 pb-6 ${idx < 2 ? "border-l-2 ml-[15px]" : "ml-[15px]"} ${
                            completed ? "border-primary" : "border-border"
                          }`}
                        >
                          {/* Node */}
                          <div
                            className={`absolute left-[-13px] top-0 h-[26px] w-[26px] rounded-full flex items-center justify-center border-2 ${
                              completed
                                ? "bg-primary border-primary"
                                : active
                                ? "bg-card border-primary"
                                : "bg-card border-border"
                            }`}
                          >
                            {completed ? (
                              <Check className="h-3.5 w-3.5 text-primary-foreground" />
                            ) : (
                              <span className={`text-[10px] font-display ${active ? "text-primary" : "text-muted-foreground"}`}>
                                {s.step}
                              </span>
                            )}
                          </div>

                          <h4 className={`text-sm font-display font-medium ${active || completed ? "text-foreground" : "text-muted-foreground"}`}>
                            {s.title}
                          </h4>
                          {(active || completed) && s.content}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {aaStep < 3 && aaStep > 0 && (
                  <Button
                    onClick={advanceAA}
                    variant="outline"
                    size="sm"
                    className="mt-2 font-display text-xs border-primary/30 text-primary hover:bg-primary/10"
                  >
                    Simulate Next Step
                  </Button>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="mt-8">
        <button className="w-full relative overflow-hidden bg-primary text-primary-foreground font-display font-semibold text-sm py-4 rounded-lg hover:bg-primary/90 transition-colors group">
          <span className="relative z-10 flex items-center justify-center gap-2">
            <Rocket className="h-4 w-4" />
            Launch Analysis
          </span>
          <div className="absolute inset-0 animate-shimmer opacity-0 group-hover:opacity-100 transition-opacity" />
        </button>
      </div>
    </div>
  );
}
