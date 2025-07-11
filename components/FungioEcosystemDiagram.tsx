import React from 'react';

const FungioEcosystemDiagram = () => {
  return (
    <div className="my-12 flex flex-col items-center font-body">
      <div className="w-full max-w-md rounded-lg border-2 border-glow-mint/80 bg-glow-mint/10 p-4 text-center font-semibold shadow-[0_0_20px_rgba(140,255,218,0.3)]">
        App UI (Fungio)
      </div>
      <div className="my-2 text-4xl text-glow-mint">↓</div>
      <div className="w-full max-w-md rounded-lg border-2 border-neural-violet/80 bg-neural-violet/10 p-4 text-center font-semibold shadow-[0_0_20px_rgba(122,92,255,0.3)]">
        Kaeluun Symbolic Layer
      </div>
      <div className="my-2 text-4xl text-glow-mint">↓</div>
      <div className="w-full max-w-md rounded-lg border-2 border-white/30 bg-white/5 p-4 text-center font-semibold">
        Transport Layer (BLE, GPS, WiFi Direct)
      </div>
    </div>
  );
};

export default FungioEcosystemDiagram;
