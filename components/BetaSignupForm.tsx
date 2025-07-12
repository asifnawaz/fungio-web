import React, { useState } from 'react';
import { motion } from 'framer-motion';
import FungalButton from './FungalButton';

interface BetaSignupFormProps {
  className?: string;
}

const BetaSignupForm: React.FC<BetaSignupFormProps> = ({ className = '' }) => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');

    try {
      const response = await fetch('/api/beta-signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(`Welcome to the organism! You're #${data.data.position} in the beta queue.`);
        setEmail('');
      } else {
        setStatus('error');
        setMessage(data.message || 'Something went wrong. Please try again.');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please check your connection and try again.');
    }
  };



  if (status === 'success') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`text-center p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-glow-mint/10 to-neural-violet/10 border border-glow-mint/20 ${className}`}
      >
        <div className="text-4xl sm:text-6xl mb-3 sm:mb-4">🍄</div>
        <h3 className="text-xl sm:text-2xl font-heading font-bold text-glow-mint mb-2">
          You're In!
        </h3>
        <p className="text-sm sm:text-base text-muted-white/80 mb-3 sm:mb-4">{message}</p>
        <p className="text-xs sm:text-sm text-muted-white/60">
          We'll reach out when the mycelial network is ready to grow.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.form
      onSubmit={handleSubmit}
      className={`space-y-4 sm:space-y-6 ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Mobile: Stacked layout, Desktop: Side-by-side */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-0 max-w-md mx-auto">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="flex-1 px-4 sm:px-6 py-4 sm:py-4 rounded-lg sm:rounded-l-lg sm:rounded-r-none bg-fungal-dark/50 border-2 sm:border-r-0 border-glow-mint/20 text-white placeholder-muted-white/50 focus:outline-none focus:border-glow-mint/50 focus:ring-2 focus:ring-glow-mint/20 transition-all duration-300 text-base"
          placeholder="your@email.com"
          disabled={status === 'loading'}
        />
        <button
          type="submit"
          disabled={status === 'loading' || !email}
          className="bg-glow-mint text-fungal-dark font-bold font-heading py-4 px-6 sm:px-8 rounded-lg sm:rounded-l-none sm:rounded-r-lg hover:bg-neural-violet hover:text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed text-base sm:text-sm whitespace-nowrap min-h-[52px] flex items-center justify-center"
        >
          {status === 'loading' ? 'Joining...' : 'Join Beta'}
        </button>
      </div>

      {status === 'error' && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
        >
          {message}
        </motion.div>
      )}



      <p className="text-xs text-muted-white/50 text-center">
        By joining, you become part of the living network. No spam, just spores.
      </p>
    </motion.form>
  );
};

export default BetaSignupForm;
