import type React from "react";
import ContractorCommunicationHub from "@/components/homeowner/ContractorCommunicationHub";

interface Props {
  bidCardId: string;
  homeownerId: string;
  visible: boolean;
}

/**
 * Wrapper component to maintain consistent hook order
 * ContractorCommunicationHub is always rendered to prevent hooks order violations
 */
const ContractorCommunicationWrapper: React.FC<Props> = ({ bidCardId, homeownerId, visible }) => {
  return (
    <div style={{ display: visible ? "block" : "none" }}>
      <ContractorCommunicationHub bidCardId={bidCardId} homeownerId={homeownerId} />
    </div>
  );
};

export default ContractorCommunicationWrapper;
