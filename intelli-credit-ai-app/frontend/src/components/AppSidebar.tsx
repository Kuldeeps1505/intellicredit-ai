import { useLocation, Link } from "react-router-dom";
import {
  LayoutDashboard, Upload, Activity, BarChart3, Users, FileEdit,
  FileText, Table2, Landmark, ClipboardList, PanelLeftClose, PanelLeft,
} from "lucide-react";
import { usePipeline } from "@/contexts/PipelineContext";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarFooter, SidebarHeader, useSidebar,
} from "@/components/ui/sidebar";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const navItems = [
  { title: "Dashboard", path: "/", icon: LayoutDashboard },
  { title: "Document Upload", path: "/upload", icon: Upload },
  { title: "Agent Progress", path: "/agents", icon: Activity },
  { title: "Risk Analytics", path: "/risk", icon: BarChart3 },
  { title: "Financial Spreads", path: "/spreads", icon: Table2 },
  { title: "Bank Analytics", path: "/bank-analytics", icon: Landmark },
  { title: "Promoter Intel", path: "/promoter", icon: Users },
  { title: "Due Diligence", path: "/diligence", icon: FileEdit },
  { title: "CAM Report", path: "/report", icon: FileText },
  { title: "Audit Trail", path: "/audit", icon: ClipboardList },
];

export function AppSidebar() {
  const location = useLocation();
  const { state, toggleSidebar } = useSidebar();
  const collapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border shadow-[2px_0_8px_rgba(0,0,0,0.04)]">
      {/* Logo + Toggle */}
      <SidebarHeader className="px-3 py-4 border-b border-sidebar-border">
        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <div className="h-8 w-8 shrink-0 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-primary-foreground font-display font-bold text-sm">IC</span>
            </div>
            <button
              onClick={toggleSidebar}
              className="h-7 w-7 shrink-0 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-colors"
              title="Expand sidebar"
            >
              <PanelLeft className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <div className="h-8 w-8 shrink-0 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-display font-bold text-sm">IC</span>
              </div>
              <div className="min-w-0">
                <h1 className="font-display text-primary text-base font-bold tracking-tight leading-tight truncate">
                  IntelliCredit
                </h1>
                <p className="text-[10px] text-muted-foreground font-body truncate">
                  AI-Powered Credit Risk
                </p>
              </div>
            </div>
            <button
              onClick={toggleSidebar}
              className="h-7 w-7 shrink-0 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50 transition-colors"
              title="Collapse sidebar"
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          </div>
        )}
      </SidebarHeader>

      {/* Nav */}
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className={collapsed ? "sr-only" : ""}>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <SidebarMenuItem key={item.path}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <SidebarMenuButton
                          asChild
                          isActive={isActive}
                          className={isActive ? "bg-sidebar-accent text-primary font-medium border-l-[3px] border-l-primary pl-[calc(0.5rem-3px)]" : "border-l-[3px] border-l-transparent"}
                        >
                          <Link to={item.path}>
                            <item.icon className="h-4 w-4 shrink-0" />
                            <span className="font-body">{item.title}</span>
                          </Link>
                        </SidebarMenuButton>
                      </TooltipTrigger>
                      {collapsed && (
                        <TooltipContent side="right">{item.title}</TooltipContent>
                      )}
                    </Tooltip>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="border-t border-sidebar-border p-0">
        <div className="px-4 py-3">
          {!collapsed ? (
            <p className="text-[9px] text-muted-foreground/60 font-body">Powered by India Stack AA · GSTN</p>
          ) : (
            <div className="h-3" />
          )}
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
