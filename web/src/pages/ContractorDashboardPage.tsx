import { useNavigate } from "react-router-dom";
import ContractorDashboard from "@/components/contractor/ContractorDashboard";
import { useAuth } from "@/contexts/AuthContext";
import { BidCardProvider } from "@/contexts/BidCardContext";
import { useEffect, useState } from "react";

export default function ContractorDashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [contractorId, setContractorId] = useState<string | undefined>();

  useEffect(() => {
    // Check for demo user if no authenticated user
    const demoUser = localStorage.getItem("DEMO_USER");
    if (demoUser) {
      const parsedDemoUser = JSON.parse(demoUser);
      setContractorId(parsedDemoUser.id);
    } else if (user?.id) {
      setContractorId(user.id);
    } else {
      // No user logged in - redirect to login
      navigate("/contractor");
    }
  }, [user, navigate]);

  return (
    <BidCardProvider>
      <ContractorDashboard contractorId={contractorId} />
    </BidCardProvider>
  );
}
