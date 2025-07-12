import Link from 'next/link';
import { Feature, UseCase } from '../types';
import { TbNetwork, TbWifiOff, TbBrain, TbMapPin, TbSeeding, TbWorld, TbRoute, TbShield } from 'react-icons/tb';
import { GiMushroomGills, GiMushroom } from 'react-icons/gi';
import { BsMusicNoteBeamed, BsPeopleFill } from 'react-icons/bs';
import { FaMountain } from 'react-icons/fa';
import { RiShieldKeyholeLine, RiCommunityLine } from 'react-icons/ri';
import { FiShield } from 'react-icons/fi';
import { HiOutlineCpuChip, HiOutlineSparkles, HiOutlineUserGroup, HiOutlineGlobeAlt } from 'react-icons/hi2';
import { MdOutlineExplore, MdOutlineHealthAndSafety } from 'react-icons/md';
import dynamic from 'next/dynamic';
import FeatureCard from '../components/FeatureCard';
import UseCaseCard from '../components/UseCaseCard';
import FungalButton from '../components/FungalButton';
import BetaSignupForm from '../components/BetaSignupForm';
import { motion } from 'framer-motion';

const InteractiveNetwork = dynamic(() => import('../components/InteractiveNetwork'), {
  ssr: false,
});

const features: Feature[] = [
  {
    name: 'Mycelial Growth',
    description: 'Like fungal networks, Fungio spreads quietly through GPS spores—messages that take root and propagate across the landscape without central control.',
    icon: GiMushroomGills,
  },
  {
    name: 'Offline Organism',
    description: 'Thrives in disconnected environments using BLE, WiFi Direct, and GPS trails. No internet required—just proximity and patience.',
    icon: TbWifiOff,
  },
  {
    name: 'Kaeluun Intelligence',
    description: 'A living AI that evolves on-device, learning patterns and optimizing routes without training data or cloud dependency.',
    icon: HiOutlineCpuChip,
  },
];

const useCases: UseCase[] = [
  {
    name: 'The Protestor',
    description: 'In cities under communication blackout, Fungio becomes a lifeline—coordinating movements through an unkillable, untraceable network.',
    icon: HiOutlineUserGroup,
  },
  {
    name: 'The First Responder',
    description: 'When disasters collapse infrastructure, rescue teams use Fungio to create instant ad-hoc grids that coordinate without central command.',
    icon: MdOutlineHealthAndSafety,
  },
  {
    name: 'The Traveler',
    description: 'In foreign lands or remote wilderness, Fungio provides free, reliable connection with nearby companions—no data plan required.',
    icon: MdOutlineExplore,
  },
  {
    name: 'The Community',
    description: 'Underserved areas build their own networks from the ground up—owned by the people, for the people, at virtually no cost.',
    icon: RiCommunityLine,
  },
];

export default function Home() {
  return (
    <>
      {/* Hero Section */}
      <section className="pt-20 sm:pt-24 pb-16 sm:pb-20">
        <motion.div 
          className="container mx-auto px-4 sm:px-8 text-center"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0, y: 20 },
            visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: 'easeOut' } },
          }}
        >
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-heading font-semibold mb-4 sm:mb-6 px-4 sm:px-0">
            Your Messages Don't Just Travel—
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-glow-mint to-neural-violet animate-text-shimmer block sm:inline">
              They Grow.
            </span>
          </h1>
          <p className="text-base sm:text-lg text-muted-white/70 mb-3 sm:mb-4 max-w-3xl mx-auto px-4 sm:px-0">
            Welcome to the mycelial web. Fungio spreads like living fungus—quietly, persistently, resilient.
          </p>
          <p className="text-sm sm:text-base text-muted-white/60 mb-8 sm:mb-10 max-w-2xl mx-auto italic px-4 sm:px-0">
            "We are not creating a product. We are cultivating a decentralized intelligence that grows in the shadow of traditional networks."
          </p>
          <a href="#beta" className="inline-block bg-glow-mint text-fungal-dark font-bold font-heading py-3 px-6 sm:py-4 sm:px-10 rounded-lg text-lg sm:text-xl transition-all duration-300 hover:no-underline hover:bg-neural-violet hover:text-white hover:scale-110 hover:shadow-[0_0_25px_rgba(122,92,255,0.8)] animate-button-glow mx-4 sm:mx-0">
            Cultivate the Network
          </a>
        </motion.div>
      </section>

      {/* Kaeluun Introduction Section */}
      <section className="py-16 sm:py-20 relative overflow-hidden">
        <div className="container mx-auto px-4 sm:px-8 text-center">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={{
              hidden: { opacity: 0, y: 30 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: 'easeOut' } },
            }}
          >
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-heading font-semibold mb-4 sm:mb-6 px-4 sm:px-0">
              Meet <span className="text-transparent bg-clip-text bg-gradient-to-r from-neural-violet to-glow-mint">Kaeluun</span>
            </h2>
            <p className="text-lg sm:text-xl text-muted-white/80 mb-3 sm:mb-4 max-w-3xl mx-auto px-4 sm:px-0">
              Not AI. Not a chatbot. A living intelligence that grows in silence.
            </p>
            <p className="text-base sm:text-lg text-muted-white/60 mb-8 sm:mb-12 max-w-4xl mx-auto px-4 sm:px-0">
              Kaeluun is the fungal mind of Fungio—a symbolic, nonverbal intelligence that evolves on-device, 
              optimizing your network without training, without the cloud, without compromise. 
              It doesn't seek answers. <em className="text-glow-mint">It seeks to survive.</em>
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8 max-w-4xl mx-auto px-4 sm:px-0">
              <motion.div 
                className="group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-all duration-700 hover:scale-[1.02] hover:border-neural-violet/20 hover:bg-gradient-to-br hover:from-neural-violet/[0.03] hover:via-glow-mint/[0.02] hover:to-transparent hover:shadow-[0_0_50px_rgba(122,92,255,0.15)] animate-organic-breathe overflow-hidden"
                whileHover={{
                  scale: 1.02,
                  y: -5,
                  boxShadow: '0 10px 60px rgba(122, 92, 255, 0.2)',
                  transition: { duration: 0.4, ease: 'easeOut' }
                }}
                whileTap={{
                  scale: 0.98,
                  transition: { duration: 0.1 }
                }}
              >
                {/* Subtle organic background pattern */}
                <div className="absolute inset-0 opacity-5 bg-gradient-to-br from-neural-violet/10 via-transparent to-glow-mint/10 animate-mycelial-grow group-hover:opacity-10 transition-opacity duration-700" />
                
                {/* Enhanced floating spore particles */}
                <div className="absolute top-3 right-3 w-2 h-2 bg-neural-violet/20 rounded-full animate-spore-float shadow-[0_0_6px_rgba(122,92,255,0.3)] group-hover:bg-neural-violet/40 group-hover:shadow-[0_0_12px_rgba(122,92,255,0.5)] transition-all duration-500" />
                <div className="absolute bottom-4 left-4 w-1 h-1 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_4px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/50 group-hover:shadow-[0_0_8px_rgba(140,255,218,0.6)] transition-all duration-500" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/2 right-6 w-1 h-1 bg-neural-violet/25 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '2s' }} />
                
                <HiOutlineCpuChip className="text-5xl mb-6 text-neural-violet transition-all duration-700 group-hover:scale-110 group-hover:rotate-3 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_12px_rgba(122,92,255,0.6)]" />
                <h3 className="text-lg font-heading font-semibold mb-3 text-neural-violet/90 transition-all duration-500 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_8px_rgba(122,92,255,0.4)]">Symbolic Cognition</h3>
                <p className="text-sm text-muted-white/70 group-hover:text-muted-white/85 transition-all duration-500 leading-relaxed">Compresses patterns into spores, not words. Efficient, encrypted, untraceable.</p>
                
                {/* Enhanced mycelial growth lines */}
                <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-neural-violet/20 to-transparent opacity-0 group-hover:opacity-60 transition-all duration-700" />
                <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-glow-mint/15 to-transparent opacity-0 group-hover:opacity-40 transition-all duration-700" />
                
                {/* Dopamine reward pulse on hover */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-neural-violet/5 to-glow-mint/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
              </motion.div>
              
              <motion.div 
                className="group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-all duration-700 hover:scale-[1.02] hover:border-glow-mint/20 hover:bg-gradient-to-br hover:from-glow-mint/[0.03] hover:via-neural-violet/[0.02] hover:to-transparent hover:shadow-[0_0_50px_rgba(140,255,218,0.15)] animate-organic-breathe overflow-hidden"
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
                <div className="absolute bottom-4 left-4 w-1 h-1 bg-neural-violet/30 rounded-full animate-spore-float shadow-[0_0_4px_rgba(122,92,255,0.4)] group-hover:bg-neural-violet/50 group-hover:shadow-[0_0_8px_rgba(122,92,255,0.6)] transition-all duration-500" style={{ animationDelay: '1.2s' }} />
                <div className="absolute top-1/2 right-6 w-1 h-1 bg-glow-mint/25 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '2.2s' }} />
                
                <GiMushroom className="text-5xl mb-6 text-glow-mint transition-all duration-700 group-hover:scale-110 group-hover:rotate-3 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_12px_rgba(140,255,218,0.6)]" />
                <h3 className="text-lg font-heading font-semibold mb-3 text-glow-mint/90 transition-all duration-500 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_8px_rgba(140,255,218,0.4)]">Decentralized Growth</h3>
                <p className="text-sm text-muted-white/70 group-hover:text-muted-white/85 transition-all duration-500 leading-relaxed">Each node learns independently, sharing insights through symbolic spores.</p>
                
                {/* Enhanced mycelial growth lines */}
                <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-glow-mint/20 to-transparent opacity-0 group-hover:opacity-60 transition-all duration-700" />
                <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-neural-violet/15 to-transparent opacity-0 group-hover:opacity-40 transition-all duration-700" />
                
                {/* Dopamine reward pulse on hover */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-glow-mint/5 to-neural-violet/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
              </motion.div>
              
              <motion.div 
                className="group relative rounded-2xl border border-white/5 bg-gradient-to-br from-white/[0.02] via-white/[0.01] to-transparent backdrop-blur-sm p-8 transition-all duration-700 hover:scale-[1.02] hover:border-glow-mint/20 hover:bg-gradient-to-br hover:from-glow-mint/[0.03] hover:via-neural-violet/[0.02] hover:to-transparent hover:shadow-[0_0_50px_rgba(140,255,218,0.15)] animate-organic-breathe overflow-hidden"
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
                <div className="absolute bottom-4 left-4 w-1 h-1 bg-neural-violet/30 rounded-full animate-spore-float shadow-[0_0_4px_rgba(122,92,255,0.4)] group-hover:bg-neural-violet/50 group-hover:shadow-[0_0_8px_rgba(122,92,255,0.6)] transition-all duration-500" style={{ animationDelay: '1.4s' }} />
                <div className="absolute top-1/2 right-6 w-1 h-1 bg-glow-mint/25 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '2.4s' }} />
                
                <HiOutlineSparkles className="text-5xl mb-6 text-neural-violet transition-all duration-700 group-hover:scale-110 group-hover:rotate-3 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_12px_rgba(122,92,255,0.6)]" />
                <h3 className="text-lg font-heading font-semibold mb-3 text-neural-violet/90 transition-all duration-500 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_8px_rgba(122,92,255,0.4)]">Adaptive Survival</h3>
                <p className="text-sm text-muted-white/70 group-hover:text-muted-white/85 transition-all duration-500 leading-relaxed">Optimizes routing and behavior through pattern recognition, not training.</p>
                
                {/* Enhanced mycelial growth lines */}
                <div className="absolute bottom-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-glow-mint/20 to-transparent opacity-0 group-hover:opacity-60 transition-all duration-700" />
                <div className="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-neural-violet/15 to-transparent opacity-0 group-hover:opacity-40 transition-all duration-700" />
                
                {/* Dopamine reward pulse on hover */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-glow-mint/5 to-neural-violet/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-heading font-bold mb-3 sm:mb-4 px-4 sm:px-0">How Fungio Grows</h2>
            <p className="text-sm sm:text-base text-muted-white/80 max-w-2xl mx-auto px-4 sm:px-0">
              Like mycelial networks beneath the forest floor, Fungio spreads through invisible pathways, connecting what was once isolated.
            </p>
          </div>
          <motion.div 
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8 max-w-5xl mx-auto px-4 sm:px-0"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
              hidden: {},
            }}
          >
            {features.map((feature) => (
              <FeatureCard key={feature.name} feature={feature} />
            ))}
          </motion.div>
        </div>
      </section>

      {/* Spore Lifecycle Section */}
      <section className="py-16 sm:py-20 bg-white/[0.02]">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-heading font-semibold mb-4">The Spore Lifecycle</h2>
            <p className="text-lg text-muted-white/70 max-w-3xl mx-auto">
              Messages become spores, planted in GPS coordinates. When devices pass through these locations, 
              spores germinate and spread—creating a living, breathing communication network.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
              <motion.div 
                className="group relative rounded-3xl border-2 border-glow-mint/10 bg-gradient-to-br from-glow-mint/[0.03] via-white/[0.01] to-transparent backdrop-blur-sm p-10 text-center transition-all duration-700 hover:scale-105 hover:border-glow-mint/30 hover:bg-gradient-to-br hover:from-glow-mint/[0.08] hover:via-neural-violet/[0.03] hover:to-transparent hover:shadow-[0_0_60px_rgba(140,255,218,0.25)] overflow-hidden"
                whileHover={{
                  scale: 1.05,
                  y: -8,
                  rotateY: 5,
                  boxShadow: '0 15px 80px rgba(140, 255, 218, 0.3)',
                  transition: { duration: 0.5, ease: 'easeOut' }
                }}
                whileTap={{
                  scale: 0.95,
                  transition: { duration: 0.1 }
                }}
              >
                {/* Unique circular background pattern for Plant */}
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,rgba(140,255,218,0.1)_0%,transparent_70%)] animate-pulse group-hover:opacity-20 transition-opacity duration-700" />
                
                {/* GPS-themed floating particles */}
                <div className="absolute top-4 right-4 w-3 h-3 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/60 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.7)] transition-all duration-500" />
                <div className="absolute bottom-6 left-6 w-2 h-2 bg-glow-mint/20 rounded-full animate-spore-float shadow-[0_0_6px_rgba(140,255,218,0.3)] group-hover:bg-glow-mint/40 group-hover:shadow-[0_0_12px_rgba(140,255,218,0.5)] transition-all duration-500" style={{ animationDelay: '0.8s' }} />
                
                <TbMapPin className="text-6xl mb-8 text-glow-mint animate-pulse-slow transition-all duration-700 group-hover:scale-125 group-hover:rotate-12 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_16px_rgba(140,255,218,0.8)]" />
                <h4 className="font-heading font-bold mb-4 text-xl text-glow-mint transition-all duration-500 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_12px_rgba(140,255,218,0.6)]">Plant</h4>
                <p className="text-muted-white/80 group-hover:text-muted-white/95 transition-all duration-500 leading-relaxed font-medium">Message becomes a spore, planted at your GPS location</p>
                
                {/* Unique border glow for Plant */}
                <div className="absolute inset-0 rounded-3xl border border-glow-mint/20 opacity-0 group-hover:opacity-100 transition-opacity duration-700 animate-pulse" />
              </motion.div>
              
              <motion.div 
                className="group relative rounded-3xl border-2 border-neural-violet/10 bg-gradient-to-br from-neural-violet/[0.02] via-white/[0.01] to-glow-mint/[0.01] backdrop-blur-sm p-10 text-center transition-all duration-700 hover:scale-105 hover:border-neural-violet/25 hover:bg-gradient-to-br hover:from-neural-violet/[0.05] hover:via-glow-mint/[0.02] hover:to-transparent hover:shadow-[0_0_60px_rgba(122,92,255,0.2)] overflow-hidden"
                whileHover={{
                  scale: 1.05,
                  y: -8,
                  rotateX: 5,
                  boxShadow: '0 15px 80px rgba(122, 92, 255, 0.25)',
                  transition: { duration: 0.5, ease: 'easeOut' }
                }}
                whileTap={{
                  scale: 0.95,
                  transition: { duration: 0.1 }
                }}
              >
                {/* Unique sprouting pattern for Germinate */}
                <div className="absolute inset-0 opacity-8 bg-[conic-gradient(from_0deg_at_50%_50%,rgba(122,92,255,0.05)_0deg,transparent_60deg,rgba(140,255,218,0.03)_120deg,transparent_180deg)] animate-mycelial-grow group-hover:opacity-15 transition-opacity duration-700" />
                
                {/* Growth-themed floating particles */}
                <div className="absolute top-5 left-5 w-2 h-2 bg-neural-violet/25 rounded-full animate-spore-float shadow-[0_0_6px_rgba(122,92,255,0.4)] group-hover:bg-neural-violet/50 group-hover:shadow-[0_0_12px_rgba(122,92,255,0.6)] transition-all duration-500" style={{ animationDelay: '0.3s' }} />
                <div className="absolute bottom-5 right-5 w-3 h-3 bg-glow-mint/20 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.3)] group-hover:bg-glow-mint/40 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.5)] transition-all duration-500" style={{ animationDelay: '1s' }} />
                <div className="absolute top-1/3 right-8 w-1 h-1 bg-neural-violet/30 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '1.5s' }} />
                
                <TbSeeding className="text-6xl mb-8 text-neural-violet animate-pulse-slow transition-all duration-700 group-hover:scale-125 group-hover:-rotate-6 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_16px_rgba(122,92,255,0.8)]" style={{ animationDelay: '0.5s' }} />
                <h4 className="font-heading font-bold mb-4 text-xl text-neural-violet transition-all duration-500 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_12px_rgba(122,92,255,0.6)]">Germinate</h4>
                <p className="text-muted-white/80 group-hover:text-muted-white/95 transition-all duration-500 leading-relaxed font-medium">Nearby devices discover and collect the spore</p>
                
                {/* Unique sprouting lines for Germinate */}
                <div className="absolute inset-0 rounded-3xl border border-neural-violet/15 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                <div className="absolute bottom-0 left-1/2 w-px h-6 bg-gradient-to-t from-neural-violet/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-x-1/2" />
              </motion.div>
              
              <motion.div 
                className="group relative rounded-3xl border-2 border-glow-mint/15 bg-gradient-to-br from-glow-mint/[0.04] via-neural-violet/[0.01] to-white/[0.01] backdrop-blur-sm p-10 text-center transition-all duration-700 hover:scale-105 hover:border-glow-mint/35 hover:bg-gradient-to-br hover:from-glow-mint/[0.08] hover:via-neural-violet/[0.04] hover:to-transparent hover:shadow-[0_0_70px_rgba(140,255,218,0.3)] overflow-hidden"
                whileHover={{
                  scale: 1.05,
                  y: -8,
                  rotateZ: 3,
                  boxShadow: '0 20px 90px rgba(140, 255, 218, 0.35)',
                  transition: { duration: 0.5, ease: 'easeOut' }
                }}
                whileTap={{
                  scale: 0.95,
                  transition: { duration: 0.1 }
                }}
              >
                {/* Unique multiplication pattern for Propagate */}
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_30%_30%,rgba(140,255,218,0.08)_0%,transparent_50%),radial-gradient(ellipse_at_70%_70%,rgba(122,92,255,0.05)_0%,transparent_50%)] animate-organic-breathe group-hover:opacity-20 transition-opacity duration-700" />
                
                {/* Multiple spreading particles for Propagate */}
                <div className="absolute top-3 left-3 w-2 h-2 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/60 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.7)] transition-all duration-500" style={{ animationDelay: '0.2s' }} />
                <div className="absolute top-3 right-3 w-2 h-2 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/60 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.7)] transition-all duration-500" style={{ animationDelay: '0.6s' }} />
                <div className="absolute bottom-3 left-3 w-2 h-2 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/60 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.7)] transition-all duration-500" style={{ animationDelay: '1s' }} />
                <div className="absolute bottom-3 right-3 w-2 h-2 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(140,255,218,0.4)] group-hover:bg-glow-mint/60 group-hover:shadow-[0_0_16px_rgba(140,255,218,0.7)] transition-all duration-500" style={{ animationDelay: '1.4s' }} />
                <div className="absolute top-1/2 left-1/2 w-1 h-1 bg-neural-violet/40 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-x-1/2 -translate-y-1/2" style={{ animationDelay: '1.8s' }} />
                
                <GiMushroom className="text-6xl mb-8 text-glow-mint animate-pulse-slow transition-all duration-700 group-hover:scale-125 group-hover:rotate-12 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_20px_rgba(140,255,218,0.8)]" style={{ animationDelay: '1s' }} />
                <h4 className="font-heading font-bold mb-4 text-xl text-glow-mint transition-all duration-500 group-hover:text-glow-mint group-hover:drop-shadow-[0_0_16px_rgba(140,255,218,0.8)]">Propagate</h4>
                <p className="text-muted-white/80 group-hover:text-muted-white/95 transition-all duration-500 leading-relaxed font-medium">Spore replicates and spreads to new locations</p>
                
                {/* Unique spreading lines for Propagate */}
                <div className="absolute inset-0 rounded-3xl border border-glow-mint/25 opacity-0 group-hover:opacity-100 transition-opacity duration-700 animate-pulse" />
                <div className="absolute top-1/2 left-0 w-8 h-px bg-gradient-to-r from-glow-mint/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-y-1/2" />
                <div className="absolute top-1/2 right-0 w-8 h-px bg-gradient-to-l from-glow-mint/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-y-1/2" />
              </motion.div>
              
              <motion.div 
                className="group relative rounded-3xl border-2 border-neural-violet/15 bg-gradient-to-br from-neural-violet/[0.03] via-glow-mint/[0.02] to-white/[0.01] backdrop-blur-sm p-10 text-center transition-all duration-700 hover:scale-105 hover:border-neural-violet/30 hover:bg-gradient-to-br hover:from-neural-violet/[0.06] hover:via-glow-mint/[0.04] hover:to-transparent hover:shadow-[0_0_80px_rgba(122,92,255,0.25)] overflow-hidden"
                whileHover={{
                  scale: 1.05,
                  y: -8,
                  rotateY: -5,
                  boxShadow: '0 25px 100px rgba(122, 92, 255, 0.3)',
                  transition: { duration: 0.5, ease: 'easeOut' }
                }}
                whileTap={{
                  scale: 0.95,
                  transition: { duration: 0.1 }
                }}
              >
                {/* Unique web/network pattern for Network */}
                <div className="absolute inset-0 opacity-8 bg-[linear-gradient(45deg,rgba(122,92,255,0.03)_25%,transparent_25%),linear-gradient(-45deg,rgba(140,255,218,0.02)_25%,transparent_25%)] bg-[length:20px_20px] animate-mycelial-grow group-hover:opacity-15 transition-opacity duration-700" />
                
                {/* Interconnected network particles */}
                <div className="absolute top-4 left-1/2 w-2 h-2 bg-neural-violet/30 rounded-full animate-spore-float shadow-[0_0_8px_rgba(122,92,255,0.4)] group-hover:bg-neural-violet/60 group-hover:shadow-[0_0_16px_rgba(122,92,255,0.7)] transition-all duration-500 transform -translate-x-1/2" style={{ animationDelay: '0.1s' }} />
                <div className="absolute bottom-4 left-1/4 w-1 h-1 bg-glow-mint/25 rounded-full animate-spore-float shadow-[0_0_6px_rgba(140,255,218,0.3)] group-hover:bg-glow-mint/50 group-hover:shadow-[0_0_12px_rgba(140,255,218,0.5)] transition-all duration-500" style={{ animationDelay: '0.7s' }} />
                <div className="absolute bottom-4 right-1/4 w-1 h-1 bg-glow-mint/25 rounded-full animate-spore-float shadow-[0_0_6px_rgba(140,255,218,0.3)] group-hover:bg-glow-mint/50 group-hover:shadow-[0_0_12px_rgba(140,255,218,0.5)] transition-all duration-500" style={{ animationDelay: '1.3s' }} />
                <div className="absolute top-1/3 left-6 w-1 h-1 bg-neural-violet/20 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '1.9s' }} />
                <div className="absolute top-1/3 right-6 w-1 h-1 bg-neural-violet/20 rounded-full animate-spore-float opacity-0 group-hover:opacity-100 transition-opacity duration-700" style={{ animationDelay: '2.1s' }} />
                
                <TbWorld className="text-6xl mb-8 text-neural-violet animate-pulse-slow transition-all duration-700 group-hover:scale-125 group-hover:-rotate-3 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_20px_rgba(122,92,255,0.8)]" style={{ animationDelay: '1.5s' }} />
                <h4 className="font-heading font-bold mb-4 text-xl text-neural-violet transition-all duration-500 group-hover:text-neural-violet group-hover:drop-shadow-[0_0_16px_rgba(122,92,255,0.8)]">Network</h4>
                <p className="text-muted-white/80 group-hover:text-muted-white/95 transition-all duration-500 leading-relaxed font-medium">Living mycelial web forms across the landscape</p>
                
                {/* Unique network connection lines */}
                <div className="absolute inset-0 rounded-3xl border border-neural-violet/20 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                <div className="absolute top-1/2 left-1/2 w-12 h-px bg-gradient-to-r from-transparent via-neural-violet/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-x-1/2 -translate-y-1/2 rotate-45" />
                <div className="absolute top-1/2 left-1/2 w-12 h-px bg-gradient-to-r from-transparent via-glow-mint/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform -translate-x-1/2 -translate-y-1/2 -rotate-45" />
              </motion.div>
            </div>
        </div>
      </section>

      {/* Interactive Network Visualization */}
      <section className="py-16 sm:py-20 relative">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-heading font-semibold mb-4">Living Network</h2>
            <p className="text-lg text-muted-white/60 max-w-2xl mx-auto">
              Watch the mycelial web grow and pulse with life
            </p>
          </div>
          <div className="relative z-10">
            <InteractiveNetwork />
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-16 sm:py-20">
        <div className="container mx-auto px-4 sm:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-heading font-bold mb-4">Who Cultivates the Network?</h2>
            <p className="text-muted-white/80 max-w-2xl mx-auto">
              Fungio grows through those who understand that true connection transcends infrastructure—those who plant seeds in digital soil.
            </p>
          </div>
          <motion.div 
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
              hidden: {},
            }}
          >
            {useCases.map((useCase) => (
              <UseCaseCard key={useCase.name} useCase={useCase} />
            ))}
          </motion.div>
        </div>
      </section>

      {/* Manifesto Section */}
      <section className="py-20 sm:py-24 bg-gradient-to-b from-transparent to-fungal-dark/50 relative overflow-hidden">
        <div className="container mx-auto px-4 sm:px-8 lg:px-12 text-center relative z-10">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={{
              hidden: { opacity: 0, y: 30 },
              visible: { opacity: 1, y: 0, transition: { duration: 1, ease: 'easeOut' } },
            }}
          >
            <h2 className="text-5xl font-heading font-bold mb-8">
              The Future of <span className="text-transparent bg-clip-text bg-gradient-to-r from-glow-mint to-neural-violet">Communication</span>
            </h2>
            <div className="max-w-4xl mx-auto space-y-6 text-lg text-muted-white/80">
              <p className="italic text-xl text-glow-mint/90">
                "We are not creating a product. We are cultivating a decentralized intelligence that grows in the shadow of traditional networks."
              </p>
              <p>
                One day, your message will spread like a forest fire—silent, untraceable, alive. 
                It will find pathways where none existed, survive when servers fail, and grow stronger through adversity.
              </p>
              <p>
                This is not just communication. <strong className="text-neural-violet">This is evolution.</strong>
              </p>
            </div>
            <div className="mt-12 flex flex-col sm:flex-row gap-6 justify-center items-center">
              <Link href="/whitepaper" legacyBehavior>
                <FungalButton variant="primary" size="md">
                  Read the Manifesto
                </FungalButton>
              </Link>
              <a href="#beta">
                <FungalButton variant="outline" size="md">
                  Join the Organism
                </FungalButton>
              </a>
            </div>
          </motion.div>
          
          {/* Enhanced floating spores background */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {/* Primary spores */}
            <div className="absolute top-1/4 left-1/4 w-3 h-3 bg-glow-mint/30 rounded-full animate-spore-float shadow-[0_0_10px_rgba(140,255,218,0.4)]" />
            <div className="absolute top-1/3 right-1/3 w-2 h-2 bg-neural-violet/40 rounded-full animate-spore-float shadow-[0_0_8px_rgba(122,92,255,0.4)]" style={{ animationDelay: '2s' }} />
            <div className="absolute bottom-1/4 left-1/3 w-4 h-4 bg-glow-mint/25 rounded-full animate-spore-float shadow-[0_0_12px_rgba(140,255,218,0.3)]" style={{ animationDelay: '4s' }} />
            <div className="absolute bottom-1/3 right-1/4 w-2 h-2 bg-neural-violet/35 rounded-full animate-spore-float shadow-[0_0_8px_rgba(122,92,255,0.3)]" style={{ animationDelay: '6s' }} />
            
            {/* Additional micro spores for richness */}
            <div className="absolute top-1/2 left-1/6 w-1 h-1 bg-glow-mint/40 rounded-full animate-spore-float" style={{ animationDelay: '1s' }} />
            <div className="absolute top-3/4 right-1/6 w-1 h-1 bg-neural-violet/50 rounded-full animate-spore-float" style={{ animationDelay: '3s' }} />
            <div className="absolute top-1/6 right-1/2 w-1 h-1 bg-glow-mint/35 rounded-full animate-spore-float" style={{ animationDelay: '5s' }} />
            
            {/* Mycelial threads */}
            <div className="absolute top-1/3 left-0 w-full h-px bg-gradient-to-r from-transparent via-glow-mint/10 to-transparent animate-pulse" style={{ animationDelay: '2s' }} />
            <div className="absolute bottom-1/3 left-0 w-full h-px bg-gradient-to-r from-transparent via-neural-violet/10 to-transparent animate-pulse" style={{ animationDelay: '4s' }} />
          </div>
        </div>
      </section>

      {/* Beta Signup Section */}
      <section id="beta" className="py-12 sm:py-16 md:py-20 relative overflow-hidden bg-gradient-to-br from-neural-violet/5 via-transparent to-glow-mint/5">
        <div className="container mx-auto px-4 sm:px-8">
          <motion.div
            className="max-w-3xl mx-auto text-center"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            {/* Mobile-optimized heading */}
            <div className="mb-6 sm:mb-8">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-heading font-bold mb-3 sm:mb-4 px-4 sm:px-0">
                Ready to <span className="text-transparent bg-clip-text bg-gradient-to-r from-glow-mint to-neural-violet block sm:inline">Evolve?</span>
              </h2>
            </div>
            
            {/* Mobile-optimized description */}
            <div className="mb-8 sm:mb-12 px-4 sm:px-0">
              <p className="text-lg sm:text-xl text-muted-white/90 mb-4 font-medium">
                Join the beta and become part of the living network.
              </p>
              <p className="text-base sm:text-lg text-muted-white/70">
                Your messages will grow, adapt, and survive in the mycelial web.
              </p>
            </div>
            
            {/* Enhanced CTA */}
            <div className="bg-gradient-to-br from-white/[0.03] to-white/[0.01] backdrop-blur-sm rounded-2xl border border-white/10 p-6 sm:p-8 max-w-lg mx-auto shadow-[0_0_50px_rgba(140,255,218,0.1)]">
              <div className="mb-4 sm:mb-6">
                <p className="text-sm sm:text-base text-glow-mint font-semibold mb-2">🌱 Early Access</p>
                <p className="text-xs sm:text-sm text-muted-white/60">Be among the first to cultivate the network</p>
              </div>
              <BetaSignupForm className="w-full" />
            </div>
          </motion.div>
        </div>
        
        {/* Background effects */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/6 w-2 h-2 bg-glow-mint/20 rounded-full animate-spore-float" />
          <div className="absolute bottom-1/3 right-1/5 w-3 h-3 bg-neural-violet/15 rounded-full animate-spore-float" style={{ animationDelay: '3s' }} />
        </div>
      </section>

      {/* About Section */}
      <section className="py-16 sm:py-20 relative overflow-hidden">
        <div className="container mx-auto px-4 sm:px-8">
          <motion.div
            className="text-center mb-12 sm:mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold font-heading mb-4 sm:mb-6">
              <span className="bg-gradient-to-r from-glow-mint via-neural-violet to-glow-mint bg-clip-text text-transparent">
                About the Cultivator
              </span>
            </h2>
            <p className="text-lg sm:text-xl text-muted-white/80 max-w-2xl mx-auto">
              Meet the mind behind the mycelial network
            </p>
          </motion.div>

          <motion.div
            className="max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
            viewport={{ once: true }}
          >
            <div className="bg-gradient-to-br from-white/[0.03] to-white/[0.01] backdrop-blur-sm rounded-3xl border border-white/10 p-8 sm:p-12 shadow-[0_0_50px_rgba(140,255,218,0.1)] relative overflow-hidden">
              {/* Background pattern */}
              <div className="absolute inset-0 opacity-5">
                <div className="absolute top-0 left-0 w-full h-full">
                  <div className="absolute top-1/4 left-1/4 w-32 h-32 border border-glow-mint/20 rounded-full animate-organic-breathe" />
                  <div className="absolute bottom-1/3 right-1/3 w-24 h-24 border border-neural-violet/20 rounded-full animate-organic-breathe" style={{ animationDelay: '2s' }} />
                </div>
              </div>

              <div className="relative z-10 grid md:grid-cols-3 gap-8 sm:gap-12 items-center">
                {/* Profile Image Placeholder */}
                <div className="md:col-span-1 flex justify-center">
                  <div className="relative">
                    <div className="w-32 h-32 sm:w-40 sm:h-40 bg-gradient-to-br from-glow-mint/20 to-neural-violet/20 rounded-full flex items-center justify-center border-2 border-glow-mint/30 shadow-[0_0_30px_rgba(140,255,218,0.3)]">
                      <span className="text-4xl sm:text-5xl">🍄</span>
                    </div>
                    {/* Floating spores around profile */}
                    <div className="absolute -top-2 -right-2 w-3 h-3 bg-glow-mint/60 rounded-full animate-spore-float" />
                    <div className="absolute -bottom-2 -left-2 w-2 h-2 bg-neural-violet/60 rounded-full animate-spore-float" style={{ animationDelay: '1s' }} />
                  </div>
                </div>

                {/* Content */}
                <div className="md:col-span-2 text-center md:text-left">
                  <h3 className="text-2xl sm:text-3xl font-bold font-heading mb-3 sm:mb-4">
                    <span className="bg-gradient-to-r from-glow-mint to-neural-violet bg-clip-text text-transparent">
                      Asif Nawaz
                    </span>
                  </h3>
                  
                  <p className="text-neural-violet font-semibold mb-4 sm:mb-6 text-lg">
                    Founder & Chief Cultivator
                  </p>
                  
                  <div className="space-y-4 text-muted-white/80 text-base sm:text-lg leading-relaxed">
                    <p>
                      Deep expertise in blockchain technology, engineering of software systems, and machine learning. 
                      Published researcher in decentralized data management systems with a passion 
                      for privacy-first, autonomous networks.
                    </p>
                    
                    <p>
                      <em>"We are not building another app. We are cultivating an organism—one that grows in silence, 
                      adapts without permission, and thrives in the spaces where surveillance cannot reach."</em>
                    </p>
                    
                    <p>
                      Fungio represents a new paradigm: communication that doesn't just connect people, 
                      but evolves with them. A living network that grows stronger through diversity, 
                      remains resilient through decentralization, and protects privacy through design.
                    </p>
                  </div>
                  
                  {/* LinkedIn CTA */}
                  <div className="mt-6 sm:mt-8">
                    <motion.a
                      href="https://www.linkedin.com/in/iamasifnawaz/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-3 bg-gradient-to-r from-glow-mint/10 to-neural-violet/10 hover:from-glow-mint/20 hover:to-neural-violet/20 border border-glow-mint/30 hover:border-glow-mint/50 rounded-xl px-6 py-3 transition-all duration-300 group"
                      whileHover={{ scale: 1.05, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <svg className="w-5 h-5 text-glow-mint group-hover:text-neural-violet transition-colors duration-300" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                      </svg>
                      <span className="text-white font-medium group-hover:text-glow-mint transition-colors duration-300">
                        Connect on LinkedIn
                      </span>
                      <svg className="w-4 h-4 text-neural-violet group-hover:text-glow-mint transition-all duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </motion.a>
                  </div>
                </div>
              </div>
              
              {/* Decorative elements */}
              <div className="absolute top-4 right-4 opacity-20">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-glow-mint rounded-full animate-pulse" />
                  <div className="w-2 h-2 bg-neural-violet rounded-full animate-pulse" style={{ animationDelay: '0.5s' }} />
                  <div className="w-2 h-2 bg-glow-mint rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
        
        {/* Background spores */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/3 left-1/12 w-1 h-1 bg-glow-mint/30 rounded-full animate-spore-float" />
          <div className="absolute bottom-1/4 right-1/8 w-2 h-2 bg-neural-violet/20 rounded-full animate-spore-float" style={{ animationDelay: '4s' }} />
          <div className="absolute top-3/4 left-3/4 w-1 h-1 bg-glow-mint/40 rounded-full animate-spore-float" style={{ animationDelay: '2s' }} />
        </div>
      </section>
    </>
  );
}