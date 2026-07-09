import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router";
import { useEffect } from "react";
import LoginPage from "./pages/LoginPage";
import ChatPage from "./pages/ChatPage";
import SetupWizard from "./pages/setup/SetupWizard";
import AgentsPage from "./pages/agents/AgentsPage";
import UsersPage from "./pages/users/UsersPage";
import SettingsPage from "./pages/settings/SettingsPage";
import ProfilePage from "./pages/profile/ProfilePage";
import AddonAgentPage from "./pages/addon/AddonAgentPage";
import DashboardPage from "./pages/dashboard/DashboardPage";
import WorkflowPage from "./pages/workflow/WorkflowPage";
import WorkflowBuilderPage from "./pages/workflow/WorkflowBuilderPage";
import RagPage from "./pages/rag/RagPage";
import PlaygroundPage from "./pages/playground/PlaygroundPage";
import GuardrailsPage from "./pages/guardrails/GuardrailsPage";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/layout/AppLayout";
import { getSetupStatus } from "./api/setup";

function SetupGuardOutlet() {
  const navigate = useNavigate();
  useEffect(() => {
    getSetupStatus()
      .then((status) => {
        if (!status.has_supervisor) navigate("/setup", { replace: true });
      })
      .catch(() => {});
  }, []);
  return <Outlet />;
}

function LayoutRoute({ children }: { children: React.ReactNode }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/setup" element={<SetupWizard />} />

      <Route element={<SetupGuardOutlet />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/chat" element={<LayoutRoute><ChatPage /></LayoutRoute>} />
        {/* 에이전트 관리는 마켓플레이스로 통합됨 — /agents 는 하위호환 리다이렉트 */}
        <Route path="/agents" element={<Navigate to="/marketplace" replace />} />
        <Route path="/users" element={<LayoutRoute><UsersPage /></LayoutRoute>} />
        <Route path="/settings" element={<LayoutRoute><SettingsPage /></LayoutRoute>} />
        <Route path="/profile" element={<LayoutRoute><ProfilePage /></LayoutRoute>} />
        <Route path="/addon/:agentKey" element={<LayoutRoute><AddonAgentPage /></LayoutRoute>} />
        <Route path="/dashboard" element={<LayoutRoute><DashboardPage /></LayoutRoute>} />
        {/* 마켓플레이스 = 통합 에이전트 허브(내장/시스템/Addon 탭 + 자산 카탈로그) */}
        <Route path="/marketplace" element={<LayoutRoute><AgentsPage /></LayoutRoute>} />
        <Route path="/workflow" element={<LayoutRoute><WorkflowPage /></LayoutRoute>} />
        {/* impl/32(§7.2.8) — Flowise/Dify 준용 풀스크린 빌더(신규/기존 편집) */}
        <Route path="/workflow/builder" element={<LayoutRoute><WorkflowBuilderPage /></LayoutRoute>} />
        <Route path="/workflow/builder/:id" element={<LayoutRoute><WorkflowBuilderPage /></LayoutRoute>} />
        <Route path="/rag" element={<LayoutRoute><RagPage /></LayoutRoute>} />
        <Route path="/playground" element={<LayoutRoute><PlaygroundPage /></LayoutRoute>} />
        <Route path="/guardrails" element={<LayoutRoute><GuardrailsPage /></LayoutRoute>} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
