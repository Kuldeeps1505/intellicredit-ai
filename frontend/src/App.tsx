import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { DatasetProvider } from "@/contexts/DatasetContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { AppLayout } from "@/components/AppLayout";
import Dashboard from "@/pages/Dashboard";
import DocumentUpload from "@/pages/DocumentUpload";
import AgentProgress from "@/pages/AgentProgress";
import RiskAnalytics from "@/pages/RiskAnalytics";
import PromoterIntel from "@/pages/PromoterIntel";
import DueDiligence from "@/pages/DueDiligence";
import CamReport from "@/pages/CamReport";
import FinancialSpreads from "@/pages/FinancialSpreads";
import BankStatementAnalytics from "@/pages/BankStatementAnalytics";
import AuditTrail from "@/pages/AuditTrail";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <ThemeProvider>
        <DatasetProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<DocumentUpload />} />
                <Route path="/agents" element={<AgentProgress />} />
                <Route path="/risk" element={<RiskAnalytics />} />
                <Route path="/spreads" element={<FinancialSpreads />} />
                <Route path="/bank-analytics" element={<BankStatementAnalytics />} />
                <Route path="/promoter" element={<PromoterIntel />} />
                <Route path="/diligence" element={<DueDiligence />} />
                <Route path="/report" element={<CamReport />} />
                <Route path="/audit" element={<AuditTrail />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
        </DatasetProvider>
      </ThemeProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
