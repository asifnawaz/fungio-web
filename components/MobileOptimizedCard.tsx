import React from 'react';
import { motion } from 'framer-motion';

interface MobileOptimizedCardProps {
  children: React.ReactNode;
  className?: string;
  reduceAnimations?: boolean;
}

const MobileOptimizedCard: React.FC<MobileOptimizedCardProps> = ({ 
  children, 
  className = '',
  reduceAnimations = false 
}) => {
  // Detect if user prefers reduced motion
  const prefersReducedMotion = typeof window !== 'undefined' && 
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const shouldReduceAnimations = reduceAnimations || prefersReducedMotion;

  if (shouldReduceAnimations) {
    // Static version for better performance
    return (
      <div className={`group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-colors duration-300 hover:border-glow-mint/20 ${className}`}>
        {children}
      </div>
    );
  }

  // Full animation version for desktop
  return (
    <motion.div 
      className={`group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-all duration-500 hover:border-glow-mint/20 hover:bg-gradient-to-br hover:from-glow-mint/[0.02] hover:via-neural-violet/[0.01] hover:to-transparent ${className}`}
      whileHover={{
        scale: 1.01,
        y: -2,
        transition: { duration: 0.2, ease: 'easeOut' }
      }}
    >
      {children}
    </motion.div>
  );
};

export default MobileOptimizedCard;
