import { motion } from 'framer-motion';
import { Feature } from '../types';

interface FeatureCardProps {
  feature: Feature;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ feature }) => {
  const Icon = feature.icon;
  return (
    <motion.div
      className="group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-all duration-700 hover:scale-[1.02] hover:border-glow-mint/20 hover:bg-gradient-to-br hover:from-glow-mint/[0.03] hover:via-neural-violet/[0.02] hover:to-transparent hover:shadow-[0_0_50px_rgba(140,255,218,0.15)] animate-organic-breathe overflow-hidden"
      variants={{
        hidden: { opacity: 0, y: 30, scale: 0.95 },
        visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.8, ease: 'easeOut' } },
      }}
      whileHover={{
        scale: 1.02,
        y: -5,
        boxShadow: '0 10px 60px rgba(140, 255, 218, 0.2)',
        transition: { duration: 0.4, ease: 'easeOut' }
      }}
      whileTap={{
        scale: 0.98,
        transition: { duration: 0.1 }
      }}
    >
      {/* Subtle organic background pattern */}
      <div className="absolute inset-0 opacity-5 bg-gradient-to-br from-glow-mint/10 via-transparent to-neural-violet/10 animate-mycelial-grow group-hover:opacity-10 transition-opacity duration-700" />
      
      {/* Enhanced floating spore particles */}
      <div className="absolute top-3 right-3 w-2 h-2 bg-glow-mint/20 rounded-full animate-spore-float shadow-[0_0_6px_rgba(140,255,218,0.3)] group-hover:bg-glow-mint/40 group-hover:shadow-[0_0_12px_rgba(140,255,218,0.5)] transition-all duration-500" />
      <div className="absolute bottom-4 left-4 w-1 h-1 bg-neural-violet/30 rounded-full animate-spore-float shadow-[0_0_4px_rgba(122,92,255,0.4)] group-hover:bg-neural-violet/50 group-hover:shadow-[0_0_8px_rgba(122,92,255,0.6)] transition-all duration-500" style={{ animationDelay: '1s' }} />
      <div className="absolute top-1/2 right-6 w-1 h-1 bg-glow-mint/25 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '2s' }} />
      
      <Icon className="h-14 w-14 mb-6 text-glow-mint/80 transition-all duration-700 group-hover:scale-110 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_12px_rgba(140,255,218,0.6)] group-hover:rotate-3 animate-pulse-slow" />
      <h3 className="text-xl font-heading font-semibold mb-4 text-glow-mint/90 transition-all duration-500 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_8px_rgba(140,255,218,0.4)]">{feature.name}</h3>
      <p className="text-muted-white/70 group-hover:text-muted-white/85 transition-all duration-500 leading-relaxed">{feature.description}</p>
      
      {/* Enhanced mycelial growth lines */}
      <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-glow-mint/20 to-transparent opacity-0 group-hover:opacity-60 transition-all duration-700" />
      <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-neural-violet/15 to-transparent opacity-0 group-hover:opacity-40 transition-all duration-700" />
      
      {/* Dopamine reward pulse on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-glow-mint/5 to-neural-violet/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
    </motion.div>
  );
};

export default FeatureCard;
