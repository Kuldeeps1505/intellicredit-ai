import { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePipeline } from "@/contexts/PipelineContext";
import { cn } from "@/lib/utils";

type Message = { role: "user" | "assistant"; content: string };

const SUGGESTIONS = [
  "What's the current risk score?",
  "Explain DSCR ratio",
  "How do I navigate to financials?",
  "Summarize the borrower profile",
];

function getSmartReply(input: string, companyName: string, riskScore: number): string {
  const q = input.toLowerCase();

  if (q.includes("risk") && q.includes("score"))
    return `The current risk score for **${companyName}** is **${riskScore}/100**. ${riskScore >= 70 ? "This is in the safe zone — strong creditworthiness." : riskScore >= 50 ? "This falls in the moderate zone — review flagged items on the Risk Analytics page." : "This is in the high-risk zone — proceed with caution. Check Risk Analytics for details."}`;

  if (q.includes("dscr"))
    return "**DSCR (Debt Service Coverage Ratio)** measures a company's ability to service its debt. A DSCR > 1.25 is generally considered healthy. You can view detailed DSCR trends on the **Financial Spreads** page.";

  if (q.includes("navigate") || q.includes("financial") || q.includes("spread"))
    return "You can access **Financial Spreads** from the sidebar. It shows P&L, Balance Sheet, and key ratios across multiple years.";

  if (q.includes("borrower") || q.includes("profile") || q.includes("promoter"))
    return `**${companyName}** — visit the **Promoter Intel** page for entity networks, director backgrounds, and compliance flags.`;

  if (q.includes("bank") || q.includes("statement"))
    return "Head to **Bank Analytics** in the sidebar for ABB analysis, cash flow patterns, and transaction categorization.";

  if (q.includes("cam") || q.includes("report"))
    return "The **CAM Report** page compiles all analysis into a single credit appraisal memorandum. You can also export it as a PDF.";

  if (q.includes("audit") || q.includes("trail"))
    return "The **Audit Trail** page logs every agent action, data extraction, and scoring decision with timestamps.";

  if (q.includes("hello") || q.includes("hi") || q.includes("hey"))
    return `Hello! I'm your IntelliCredit AI assistant. I can help you understand **${companyName}**'s credit profile, explain metrics, or navigate the platform.`;

  return `I can help with credit analysis for **${companyName}**, explain financial metrics, or guide you through the platform. Try asking about the risk score, DSCR, or how to navigate to a specific page.`;
}

export function AiChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Use real application data — no demo fallback needed here
  const { application } = usePipeline();
  const companyName = application?.companyName ?? "the borrower";
  const riskScore   = application?.score ?? 0;

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{
        role: "assistant",
        content: `Welcome! I'm your **IntelliCredit AI** assistant. I can help analyze **${companyName}**'s credit profile or guide you through the platform. What would you like to know?`,
      }]);
    }
  }, [open, companyName]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typing]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const send = (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: text.trim() }]);
    setInput("");
    setTyping(true);
    setTimeout(() => {
      const reply = getSmartReply(text, companyName, riskScore);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
      setTyping(false);
    }, 600 + Math.random() * 800);
  };

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-lg transition-all duration-300",
          "bg-primary text-primary-foreground hover:scale-110 hover:shadow-primary/40",
          "flex items-center justify-center",
          open && "rotate-90 scale-90"
        )}
      >
        {open ? <X className="h-6 w-6" /> : <MessageSquare className="h-6 w-6" />}
      </button>

      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-[380px] max-h-[520px] flex flex-col rounded-2xl border border-border bg-card shadow-2xl shadow-black/10 animate-in slide-in-from-bottom-4 fade-in duration-300">
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border bg-secondary/50 rounded-t-2xl">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-display font-semibold text-foreground">IntelliCredit AI</p>
              <p className="text-[10px] text-muted-foreground">Credit Analysis & Navigation</p>
            </div>
            <span className="flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-safe opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-safe" />
            </span>
          </div>

          <ScrollArea className="flex-1 max-h-[340px]" ref={scrollRef}>
            <div className="p-4 space-y-3">
              {messages.map((msg, i) => (
                <div key={i} className={cn("flex gap-2", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                    <div className="h-6 w-6 rounded-full bg-primary/15 flex items-center justify-center shrink-0 mt-0.5">
                      <Bot className="h-3 w-3 text-primary" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[75%] rounded-xl px-3 py-2 text-xs leading-relaxed",
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground rounded-br-sm"
                        : "bg-secondary text-foreground rounded-bl-sm"
                    )}
                    dangerouslySetInnerHTML={{
                      __html: msg.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-primary">$1</strong>')
                        .replace(/\n/g, "<br/>"),
                    }}
                  />
                  {msg.role === "user" && (
                    <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center shrink-0 mt-0.5">
                      <User className="h-3 w-3 text-muted-foreground" />
                    </div>
                  )}
                </div>
              ))}
              {typing && (
                <div className="flex gap-2">
                  <div className="h-6 w-6 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                    <Bot className="h-3 w-3 text-primary" />
                  </div>
                  <div className="bg-secondary rounded-xl px-4 py-2 flex gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {messages.length <= 1 && (
            <div className="px-4 pb-2 flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="text-[10px] px-2.5 py-1 rounded-full border border-border bg-secondary/50 text-muted-foreground hover:text-foreground hover:border-primary/40 transition-colors">
                  {s}
                </button>
              ))}
            </div>
          )}

          <div className="p-3 border-t border-border flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              placeholder="Ask about credit analysis..."
              className="text-xs h-9 bg-secondary/50 border-border"
            />
            <Button size="icon" className="h-9 w-9 shrink-0" onClick={() => send(input)} disabled={!input.trim()}>
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
