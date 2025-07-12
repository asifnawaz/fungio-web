import Link from 'next/link';
import { ReactNode, useState } from 'react';
import FungalNetworkBackground from './FungalNetworkBackground';
import { HiMenu, HiX } from 'react-icons/hi';

interface LayoutProps {
  children?: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <div className="min-h-screen font-body relative z-0">
      <FungalNetworkBackground />
      <header className="py-4 sm:py-6 px-4 sm:px-8 flex justify-between items-center relative z-50 bg-fungal-dark/80 backdrop-blur-sm border-b border-white/5">
        <Link href="/" className="text-2xl sm:text-3xl font-heading font-semibold text-glow-mint hover:text-neural-violet transition-colors">
          Fungio
        </Link>
        
        {/* Desktop Navigation */}
        <nav className="hidden md:flex space-x-8">
          <Link href="/" className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline font-medium">Home</Link>
          <Link href="/whitepaper" className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline font-medium">Whitepaper</Link>
          <Link href="/#beta" className="bg-glow-mint text-fungal-dark px-4 py-2 rounded-lg hover:bg-neural-violet hover:text-white transition-all duration-300 hover:no-underline font-bold text-sm">Join Beta</Link>
        </nav>
        
        {/* Mobile Menu Button */}
        <button 
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden p-2 text-glow-mint hover:text-neural-violet transition-colors"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <HiX size={28} /> : <HiMenu size={28} />}
        </button>
        
        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="absolute top-full left-0 right-0 bg-fungal-dark/95 backdrop-blur-md border-b border-white/10 md:hidden">
            <nav className="flex flex-col py-4 px-4 space-y-4">
              <Link 
                href="/" 
                className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline font-medium py-2 px-4 rounded-lg hover:bg-white/5"
                onClick={() => setIsMenuOpen(false)}
              >
                Home
              </Link>
              <Link 
                href="/whitepaper" 
                className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline font-medium py-2 px-4 rounded-lg hover:bg-white/5"
                onClick={() => setIsMenuOpen(false)}
              >
                Whitepaper
              </Link>
              <Link 
                href="/#beta" 
                className="bg-glow-mint text-fungal-dark px-4 py-3 rounded-lg hover:bg-neural-violet hover:text-white transition-all duration-300 hover:no-underline font-bold text-center"
                onClick={() => setIsMenuOpen(false)}
              >
                Join Beta
              </Link>
            </nav>
          </div>
        )}
      </header>
      <main className="flex-grow container mx-auto px-4 sm:px-8 py-8 sm:py-12 prose prose-invert max-w-none">{children}</main>
      <footer className="relative z-10 border-t border-white/10 py-6 sm:py-8">
        <div className="container mx-auto px-4 sm:px-8 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-xl sm:text-2xl font-heading font-semibold text-glow-mint">
            Fungio
          </div>
          <nav className="flex flex-wrap justify-center space-x-4 sm:space-x-6 text-muted-white/80">
            <Link href="/" className="hover:text-glow-mint transition-colors hover:no-underline text-sm sm:text-base">Home</Link>
            <Link href="/whitepaper" className="hover:text-glow-mint transition-colors hover:no-underline text-sm sm:text-base">Whitepaper</Link>
            <Link href="/#beta" className="hover:text-glow-mint transition-colors hover:no-underline text-sm sm:text-base">Join Beta</Link>
          </nav>
          <div className="text-xs sm:text-sm text-muted-white/50 text-center md:text-right">
            © 2025 Fungio • Powered by Kaeluun
          </div>
        </div>
      </footer>
    </div>
  );
}