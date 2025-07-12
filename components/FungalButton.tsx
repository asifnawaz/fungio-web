import React from 'react';
import { motion } from 'framer-motion';

interface FungalButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  href?: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
}

const FungalButton = React.forwardRef<HTMLButtonElement, FungalButtonProps>(({
  children,
  variant = 'primary',
  size = 'md',
  href,
  onClick,
  className = '',
  disabled = false
}, ref) => {
  const baseClasses = "group relative inline-block font-bold font-heading transition-all duration-500 hover:no-underline overflow-hidden cursor-pointer";
  
  const variantClasses = {
    primary: "bg-gradient-to-r from-glow-mint via-glow-mint to-glow-mint/80 text-fungal-dark hover:from-neural-violet hover:via-neural-violet hover:to-glow-mint hover:text-white",
    secondary: "bg-gradient-to-r from-neural-violet via-neural-violet to-glow-mint/20 text-white hover:from-glow-mint hover:to-neural-violet hover:text-fungal-dark",
    outline: "border-2 border-glow-mint text-glow-mint bg-transparent hover:bg-glow-mint hover:text-fungal-dark hover:border-transparent"
  };
  
  const sizeClasses = {
    sm: "py-2 px-6 rounded-lg text-sm",
    md: "py-4 px-10 rounded-xl text-lg",
    lg: "py-5 px-12 rounded-2xl text-xl"
  };
  
  const shadowClasses = {
    primary: "hover:shadow-[0_0_40px_rgba(140,255,218,0.8)] hover:scale-110",
    secondary: "hover:shadow-[0_0_40px_rgba(122,92,255,0.8)] hover:scale-110", 
    outline: "hover:shadow-[0_0_40px_rgba(140,255,218,0.8)] hover:scale-110"
  };

  const buttonContent = (
    <motion.div
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${shadowClasses[variant]} ${className} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      whileHover={!disabled ? { 
        scale: 1.05,
        y: -2,
        transition: { duration: 0.2, ease: 'easeOut' }
      } : {}}
      whileTap={!disabled ? { 
        scale: 0.98,
        transition: { duration: 0.1 }
      } : {}}
      onClick={!disabled ? onClick : undefined}
    >
      {/* Enhanced glow background */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Outer glow ring */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${
        variant === 'primary' ? 'from-glow-mint to-neural-violet' :
        variant === 'secondary' ? 'from-neural-violet to-glow-mint' :
        'from-glow-mint to-neural-violet'
      } rounded-xl blur opacity-0 group-hover:opacity-40 transition-opacity duration-500`} />
      
      {/* Floating spore particles */}
      <div className="absolute top-2 right-2 w-1 h-1 bg-white/60 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      <div className="absolute bottom-2 left-2 w-1 h-1 bg-white/40 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-300" style={{ animationDelay: '0.5s' }} />
      
      {/* Content with enhanced text shadow */}
      <span className={`relative z-10 transition-all duration-500 ${
        variant === 'secondary' ? 'text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)] group-hover:text-fungal-dark group-hover:drop-shadow-none' : ''
      }`}>
        {children}
      </span>
      
      {/* Dopamine pulse effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-pulse transition-opacity duration-300" />
    </motion.div>
  );

  if (href) {
    return (
      <a href={href} className="inline-block">
        {buttonContent}
      </a>
    );
  }

  return buttonContent;
});

FungalButton.displayName = 'FungalButton';

export default FungalButton;
