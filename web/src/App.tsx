import { Toaster } from "react-hot-toast";
// Docker Live Reload Test - Agent 6
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import "./styles/agent-effects.css";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import HomeownerProjectWorkspaceFixed from "@/components/bidcards/homeowner/HomeownerProjectWorkspaceFixed";
import { AuthProvider } from "@/contexts/AuthContext";
import { IrisProvider } from "@/contexts/IrisContext";
import { AdminAuthProvider } from "@/hooks/useAdminAuth";
import { WebSocketProvider } from "@/context/WebSocketContext";
import AuthCallbackPage from "@/pages/AuthCallbackPage";
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import AdminLoginPage from "@/pages/admin/AdminLoginPage";
import AdminConnectionFeesPage from "@/pages/admin/AdminConnectionFeesPage";
import ContractorLandingPage from "@/pages/contractor/ContractorLandingPage";
import ContractorDashboardPage from "@/pages/ContractorDashboardPage";
import DashboardPage from "@/pages/DashboardPage";
import HomePage from "@/pages/HomePage";
import LoginPage from "@/pages/LoginPage";
import ProjectDetailPage from "@/pages/ProjectDetailPage";
import SignupPage from "@/pages/SignupPage";
import IntelligentMessagingTest from "@/pages/IntelligentMessagingTest";
import ContractorCOIAOnboarding from "@/pages/contractor/ContractorCOIAOnboarding";
import TestPhotoUpload from "@/pages/TestPhotoUpload";
import { BidCardProvider } from "@/contexts/BidCardContext";
import TestReactImages from "./test-react-images";
import CIABidCardDemo from "@/pages/CIABidCardDemo";
import TestPotentialBidCard from "@/pages/TestPotentialBidCard";

function App() {
  return (
    <AuthProvider>
      <IrisProvider>
        <WebSocketProvider useSharedWorker={false}>
          <Router>
            <div className="min-h-screen bg-gray-50">
            <Routes>
              <Route path="/" element={<HomePage />} />

              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="/intelligent-messaging-test" element={<IntelligentMessagingTest />} />
              <Route path="/inspiration-demo" element={<TestReactImages />} />
              <Route path="/cia-bid-card-demo" element={<CIABidCardDemo />} />
              <Route path="/test-photo-upload" element={<TestPhotoUpload />} />
              <Route path="/test-potential-bid-card" element={<TestPotentialBidCard />} />
              <Route path="/auth/callback" element={<AuthCallbackPage />} />
              <Route path="/contractor" element={<ContractorLandingPage />} />
              <Route 
                path="/contractor/dashboard" 
                element={
                  <ProtectedRoute requiredRole="contractor">
                    <BidCardProvider>
                      <ContractorDashboardPage />
                    </BidCardProvider>
                  </ProtectedRoute>
                } 
              />
              <Route path="/contractor/coia-onboarding" element={<ContractorCOIAOnboarding />} />
              <Route
                path="/admin/*"
                element={
                  <AdminAuthProvider>
                    <Routes>
                      <Route path="login" element={<AdminLoginPage />} />
                      <Route path="dashboard" element={<AdminDashboardPage />} />
                      <Route path="connection-fees" element={<AdminConnectionFeesPage />} />
                    </Routes>
                  </AdminAuthProvider>
                }
              />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute requiredRole="homeowner">
                    <DashboardPage />
                  </ProtectedRoute>
                } 
              />
              <Route
                path="/projects/:id"
                element={
                  <ProtectedRoute requiredRole="homeowner">
                    <ProjectDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/bid-cards/:id" element={<HomeownerProjectWorkspaceFixed />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <Toaster position="top-right" />
          </div>
        </Router>
        </WebSocketProvider>
      </IrisProvider>
    </AuthProvider>
  );
}

export default App;
