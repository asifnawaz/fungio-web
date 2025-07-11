import { motion, useAnimation } from 'framer-motion';
import { useState, useEffect } from 'react';

const InteractiveNetwork = () => {
  const controls = useAnimation();
  const [mousePosition, setMousePosition] = useState({ x: -1000, y: -1000 });

  const nodes = [
    { id: 0, cx: 100, cy: 150 }, { id: 1, cx: 300, cy: 100 }, { id: 2, cx: 500, cy: 150 },
    { id: 3, cx: 200, cy: 300 }, { id: 4, cx: 400, cy: 300 },
    { id: 5, cx: 150, cy: 450 }, { id: 6, cx: 350, cy: 450 }, { id: 7, cx: 550, cy: 400 },
  ];

  const paths = [
    'M 100 150 Q 200 125, 300 100', 'M 300 100 Q 400 125, 500 150',
    'M 100 150 Q 150 225, 200 300', 'M 200 300 Q 300 350, 400 300',
    'M 400 300 Q 450 225, 500 150', 'M 200 300 Q 175 375, 150 450',
    'M 400 300 Q 375 375, 350 450', 'M 350 450 Q 450 425, 550 400',
  ];

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const svgRect = event.currentTarget.getBoundingClientRect();
    setMousePosition({ x: event.clientX - svgRect.left, y: event.clientY - svgRect.top });
  };

  const handleMouseLeave = () => {
    setMousePosition({ x: -1000, y: -1000 });
  };

  useEffect(() => {
    const animation = (i: number) => {
      const node = nodes.find(n => n.id === i);
      if (!node) return {};

      const distance = Math.sqrt(Math.pow(mousePosition.x - node.cx, 2) + Math.pow(mousePosition.y - node.cy, 2));
      const maxDist = 150;
      const influence = Math.max(0, 1 - distance / maxDist);

      return {
        scale: [1, 1.5 + influence * 1.5, 1],
        transition: {
          duration: 2 - influence * 1.5,
          repeat: Infinity,
          repeatType: 'mirror' as const,
          ease: 'easeInOut' as const,
        },
      };
    };

    controls.start(animation);
  }, [mousePosition, controls, nodes]);

  return (
    <div className="w-full flex justify-center items-center">
      <svg
        viewBox="0 0 650 550"
        className="w-full max-w-4xl cursor-pointer"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="5" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
          <linearGradient id="path-gradient" gradientUnits="userSpaceOnUse" x1="100" y1="100" x2="550" y2="450">
            <stop offset="0%" stopColor="#8CFFDA" /><stop offset="100%" stopColor="#7A5CFF" />
          </linearGradient>
          <filter id="pulse-glow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="10" result="coloredBlur" />
            <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <g style={{ filter: 'url(#glow)' }}>
          {paths.map((d, i) => (
            <motion.path
              key={i} d={d} fill="none" stroke="url(#path-gradient)" strokeWidth="1"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 0.7 }}
              transition={{ 
                duration: 2 + Math.random() * 2, 
                delay: Math.random() * 1.5, 
                ease: 'circOut' as const 
              }}
            />
          ))}
          {/* Pulsing Nutrient Flow */}
          {paths.map((d, i) => (
            <motion.path
              key={`pulse-${i}`}
              d={d}
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="1.5"
              style={{ filter: 'url(#pulse-glow)' }}
              strokeDasharray="20 200"
              initial={{ strokeDashoffset: 220 }}
              animate={{ strokeDashoffset: -220 }}
              transition={{
                duration: 4 + Math.random() * 2,
                repeat: Infinity,
                repeatType: 'loop' as const,
                ease: 'linear' as const,
                delay: i * 0.5 + Math.random(),
              }}
            />
          ))}
        </g>

        <g>
          {nodes.map((node, i) => (
            <motion.circle
              key={i} cx={node.cx} cy={node.cy} r="5" fill="#8CFFDA"
              style={{ filter: 'url(#glow)' }}
              custom={node.id}
              animate={controls}
            />
          ))}
        </g>
      </svg>
    </div>
  );

};

export default InteractiveNetwork;
