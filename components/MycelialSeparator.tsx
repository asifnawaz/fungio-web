const MycelialSeparator = () => {
  return (
    <div className="w-full h-20 flex justify-center items-center my-4" aria-hidden="true">
      <svg width="80%" height="100%" viewBox="0 0 800 80" preserveAspectRatio="none">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <path
          d="M0 40 Q 100 20, 200 40 T 400 40 T 600 40 T 800 40"
          stroke="url(#separator-gradient)"
          strokeWidth="1.5"
          fill="none"
          strokeLinecap="round"
          style={{ filter: 'url(#glow)' }}
        />
        <path
          d="M100 40 Q 150 50, 200 40"
          stroke="url(#separator-gradient)"
          strokeWidth="0.5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M500 40 Q 550 30, 600 40"
          stroke="url(#separator-gradient)"
          strokeWidth="0.5"
          fill="none"
          strokeLinecap="round"
        />
        <defs>
            <linearGradient id="separator-gradient" gradientTransform="rotate(90)">
                <stop offset="0%" stopColor="rgba(122, 92, 255, 0.1)" />
                <stop offset="50%" stopColor="rgba(140, 255, 218, 0.5)" />
                <stop offset="100%" stopColor="rgba(122, 92, 255, 0.1)" />
            </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

export default MycelialSeparator;
