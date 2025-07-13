import React, { useEffect, useState } from 'react';
import { shouldReduceAnimations } from '../utils/performance';

interface MobileOptimizedSectionProps {
  children: React.ReactNode;
  className?: string;
  animatedClassName?: string;
  staticClassName?: string;
}

const MobileOptimizedSection: React.FC<MobileOptimizedSectionProps> = ({
  children,
  className = '',
  animatedClassName = '',
  staticClassName = ''
}) => {
  const [reduceAnimations, setReduceAnimations] = useState(false);

  useEffect(() => {
    setReduceAnimations(shouldReduceAnimations());
  }, []);

  const finalClassName = reduceAnimations 
    ? `${className} ${staticClassName}`.trim()
    : `${className} ${animatedClassName}`.trim();

  return (
    <div className={finalClassName}>
      {children}
    </div>
  );
};

export default MobileOptimizedSection;
