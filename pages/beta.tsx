import { useState } from 'react';

export default function Beta() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
    const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      setStatus('success');
      setMessage('Thank you! Your application has been received.');
      setEmail('');
    } catch (error) {
      setStatus('error');
      setMessage(error instanceof Error ? error.message : 'An unknown error occurred.');
    }
  };

  return (
    <>
      <div className="container mx-auto px-8 py-20 max-w-2xl text-center">
        <h1 className="text-4xl md:text-5xl font-heading font-semibold mb-4">Join the Fungio Beta</h1>
        <p className="text-lg text-muted-white/70 mb-8 max-w-2xl mx-auto">
          Be among the first to experience the future of decentralized communication. Sign up to get early access and updates.
        </p>
        <form className="max-w-md mx-auto" onSubmit={handleSubmit}>
          <div className="flex items-center">
            <input
              type="email"
              placeholder="your.email@example.com"
              className="w-full px-6 py-4 rounded-l-lg bg-white/10 border-2 border-r-0 border-white/20 focus:outline-none focus:border-glow-mint transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={status === 'loading'}
            />
            <button
              type="submit"
              className="bg-glow-mint text-fungal-dark font-bold font-heading py-4 px-8 rounded-r-lg hover:bg-neural-violet hover:text-white transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={status === 'loading'}
            >
              {status === 'loading' ? 'Submitting...' : 'Request Access'}
            </button>
          </div>
        </form>
        {message && (
          <p className={`mt-4 text-sm ${status === 'success' ? 'text-glow-mint' : 'text-red-400'}`}>
            {message}
          </p>
        )}
      </div>
    </>
  );
}
