import Link from 'next/link';
import { ReactNode } from 'react';
import FungalNetworkBackground from './FungalNetworkBackground';

interface LayoutProps {
  children?: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen font-body relative z-0">
            <FungalNetworkBackground />
      <header className="py-6 px-8 flex justify-between items-center relative z-10">
        <Link href="/" className="text-3xl font-heading font-semibold text-glow-mint">
          Fungio
        </Link>
        <nav className="space-x-8">
          <Link href="/" className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline">Home</Link>
          <Link href="/whitepaper" className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline">Whitepaper</Link>
          <Link href="/beta" className="text-muted-white hover:text-glow-mint transition-colors hover:no-underline">Apply for Beta</Link>
        </nav>
      </header>
      <main className="flex-grow container mx-auto px-8 py-12 prose prose-invert max-w-none">{children}</main>
      <footer className="relative z-10 border-t border-white/10 py-8">
        <div className="container mx-auto px-8 flex flex-col md:flex-row justify-between items-center">
          <div className="text-2xl font-heading font-semibold text-glow-mint mb-4 md:mb-0">
            Fungio
          </div>
          <nav className="flex space-x-6 text-muted-white/80 mb-4 md:mb-0">
            <Link href="/" className="hover:text-glow-mint transition-colors hover:no-underline">Home</Link>
            <Link href="/whitepaper" className="hover:text-glow-mint transition-colors hover:no-underline">Whitepaper</Link>
            <Link href="/beta" className="hover:text-glow-mint transition-colors hover:no-underline">Apply for Beta</Link>
          </nav>
          <div className="text-sm text-muted-white/50">
            © 2025 Fungio • Powered by Kaeluun
          </div>
        </div>
      </footer>
    </div>
  );
}