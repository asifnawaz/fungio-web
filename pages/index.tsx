import Link from 'next/link';
import { IconType } from 'react-icons';
import { TbNetwork, TbWifiOff, TbBrain } from 'react-icons/tb';
import { GiMushroomGills } from 'react-icons/gi';
import { BsMusicNoteBeamed, BsPeopleFill } from 'react-icons/bs';
import { FaMountain } from 'react-icons/fa';
import { RiShieldKeyholeLine } from 'react-icons/ri';
import { FiShield } from 'react-icons/fi';
import InteractiveNetwork from '../components/InteractiveNetwork';
import { motion } from 'framer-motion';


const features: { name: string; description: string; icon: IconType }[] = [
  {
    name: 'Decentralized & P2P',
    description: 'No servers, no central authority. Your conversations are yours alone, resistant to censorship and surveillance.',
    icon: TbNetwork,
  },
  {
    name: 'Offline First',
    description: 'Communicate directly with nearby devices via Bluetooth & Wi-Fi Direct, even without an internet connection.',
    icon: TbWifiOff,
  },
  {
    name: 'Privacy by Design',
    description: "End-to-end encrypted and anonymous by default. We don't know who you are, and we don't want to.",
    icon: FiShield,
  },
  {
    name: 'AI-Powered Mesh',
    description: 'Powered by Kaeluun, our on-device AI, to optimize network routing and ensure reliable message delivery.',
    icon: TbBrain,
  },
];

const useCases = [
  {
    name: 'Festival Goers',
    description: 'Lost your friends in the crowd with no cell signal? Fungio keeps your group connected when the network fails.',
    icon: BsMusicNoteBeamed,
  },
  {
    name: 'Adventurers & Hikers',
    description: 'Stay in touch with your expedition in remote locations, completely off-grid. Safety and connection, anywhere.',
    icon: FaMountain,
  },
  {
    name: 'Privacy Advocates',
    description: 'Your messages are your own. No central servers, no data collection, ever. True digital sovereignty.',
    icon: RiShieldKeyholeLine,
  },
  {
    name: 'Community Organizers',
    description: 'Build resilient, censorship-resistant communication networks for your community that can\'t be shut down.',
    icon: BsPeopleFill,
  },
];

export default function Home() {
  return (
    <>
      <motion.div 
        className="container mx-auto px-8 pt-24 pb-32 text-center"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0, y: 20 },
          visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: 'easeOut' } },
        }}
      >
        <h1 className="text-5xl md:text-6xl font-heading font-semibold mb-6">
          Connect Anonymously. <span className="text-transparent bg-clip-text bg-gradient-to-r from-glow-mint to-neural-violet animate-text-shimmer">Communicate Freely.</span>
        </h1>
        <p className="text-lg text-muted-white/70 mb-10 max-w-3xl mx-auto">
          Fungio is a revolutionary P2P messaging app that creates a private, decentralized network, inspired by the resilience of fungal mycelium.
        </p>
        <Link href="/beta" legacyBehavior>
          <a className="inline-block bg-glow-mint text-fungal-dark font-bold font-heading py-4 px-10 rounded-lg text-xl transition-all duration-300 hover:no-underline hover:bg-neural-violet hover:text-white hover:scale-110 hover:shadow-[0_0_25px_rgba(122,92,255,0.8)] animate-button-glow">
            Join the Beta
          </a>
        </Link>
      </motion.div>

      <div className="relative z-10 mt-[-6rem] mb-[-4rem]">
        <InteractiveNetwork />
      </div>
      <div className="container mx-auto px-8 pt-0 pb-20">
        <h2 className="text-4xl font-heading font-semibold text-center mb-12">Why Fungio?</h2>
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={{
            visible: { transition: { staggerChildren: 0.1 } },
            hidden: {},
          }}
        >
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <motion.div 
                key={feature.name} 
                className="group relative rounded-lg border border-white/10 bg-white/5 p-6 transition-all duration-300 hover:scale-105 hover:border-glow-mint/80 hover:bg-glow-mint/10 hover:shadow-[0_0_30px_rgba(140,255,218,0.4)]"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                {/* @ts-ignore */}
                <Icon className="h-10 w-10 mb-4 text-glow-mint transition-transform duration-300 group-hover:scale-110" />
                <h3 className="text-2xl font-heading font-semibold mb-3 text-glow-mint transition-all duration-300 group-hover:drop-shadow-[0_0_4px_rgba(140,255,218,0.5)]">{feature.name}</h3>
                <p className="text-muted-white/80">{feature.description}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      <section className="pt-16 pb-20">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-4xl font-heading font-bold mb-4">Who is Fungio For?</h2>
          <p className="text-muted-white/80 max-w-2xl mx-auto mb-12">
            Fungio is built for anyone who values connection and privacy, especially when traditional networks fail.
          </p>
          <motion.div 
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-8"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.3 }}
            variants={{
              visible: { transition: { staggerChildren: 0.1 } },
              hidden: {},
            }}
          >
            {useCases.map((useCase) => {
              const Icon = useCase.icon;
              return (
                <motion.div 
                  key={useCase.name} 
                  className="group relative rounded-lg border border-white/10 bg-white/5 p-6 transition-all duration-300 hover:scale-105 hover:border-neural-violet/80 hover:bg-neural-violet/10 hover:shadow-[0_0_30px_rgba(122,92,255,0.4)]"
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 },
                  }}
                >
                  {/* @ts-ignore */}
                  <Icon className="h-10 w-10 mb-4 text-neural-violet transition-transform duration-300 group-hover:scale-110" />
                  <h3 className="text-2xl font-heading font-semibold mb-3 text-neural-violet transition-all duration-300 group-hover:drop-shadow-[0_0_4px_rgba(122,92,255,0.5)]">{useCase.name}</h3>
                  <p className="text-muted-white/80">{useCase.description}</p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>
    </>
  );
}