import React from 'react';
import { FiEdit3, FiCpu, FiMapPin, FiZap } from 'react-icons/fi';

const LifecycleOfSporeDiagram = () => {
  return (
    <div className="my-12 flex flex-col items-center justify-center gap-4 font-body text-center md:flex-row md:gap-2">
      <div className="flex h-32 w-40 flex-col items-center justify-center rounded-lg border border-white/20 bg-white/5 p-4">
        {/* @ts-ignore */}
        <FiEdit3 className="mb-2 text-4xl text-glow-mint" />
        <span className="text-sm font-semibold">1. Message Created</span>
      </div>
      <div className="text-2xl text-neural-violet md:-mt-6">→</div>
      <div className="flex h-32 w-40 flex-col items-center justify-center rounded-lg border border-white/20 bg-white/5 p-4">
        {/* @ts-ignore */}
        <FiCpu className="mb-2 text-4xl text-neural-violet" />
        <span className="text-sm font-semibold">2. Kaeluun Compresses to Spore</span>
      </div>
      <div className="text-2xl text-neural-violet md:-mt-6">→</div>
      <div className="flex h-32 w-40 flex-col items-center justify-center rounded-lg border border-white/20 bg-white/5 p-4">
        {/* @ts-ignore */}
        <FiMapPin className="mb-2 text-4xl text-glow-mint" />
        <span className="text-sm font-semibold">3. Left at GPS Location</span>
      </div>
      <div className="text-2xl text-neural-violet md:-mt-6">→</div>
      <div className="flex h-32 w-40 flex-col items-center justify-center rounded-lg border border-white/20 bg-white/5 p-4">
        {/* @ts-ignore */}
        <FiZap className="mb-2 text-4xl text-glow-mint" />
        <span className="text-sm font-semibold">4. Discovered & Relayed</span>
      </div>
    </div>
  );
};

export default LifecycleOfSporeDiagram;
