import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';

interface SporeParticle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  size: number;
  color: string;
}

interface NetworkNode {
  id: number;
  x: number;
  y: number;
  size: number;
  connections: number[];
  type: 'hub' | 'relay' | 'endpoint';
  label: string;
  activity: number;
}

const InteractiveNetwork: React.FC = () => {
  const [hoveredNode, setHoveredNode] = useState<number | null>(null);
  const [clickedNode, setClickedNode] = useState<number | null>(null);
  const [spores, setSpores] = useState<SporeParticle[]>([]);
  const [pulseAnimation, setPulseAnimation] = useState<number | null>(null);

  // Enhanced spore generation with variety
  useEffect(() => {
    const generateSpores = () => {
      const colors = ['#8CFFDA', '#7A5CFF', '#FF6B9D', '#C4B5FD'];
      const newSpores: SporeParticle[] = [];
      for (let i = 0; i < 25; i++) {
        newSpores.push({
          id: i,
          x: Math.random() * 800,
          y: Math.random() * 400,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8,
          life: Math.random() * 100,
          size: Math.random() * 3 + 1,
          color: colors[Math.floor(Math.random() * colors.length)]
        });
      }
      setSpores(newSpores);
    };

    generateSpores();
    const interval = setInterval(() => {
      setSpores(prev => prev.map(spore => ({
        ...spore,
        x: (spore.x + spore.vx + 800) % 800,
        y: (spore.y + spore.vy + 400) % 400,
        life: (spore.life + 1) % 100
      })));
    }, 60);

    return () => clearInterval(interval);
  }, []);

  // Enhanced nodes with better positioning and hierarchy - increased sizes for better visibility
  const nodes: NetworkNode[] = [
    { id: 1, x: 150, y: 100, size: 24, type: 'hub', label: 'Mycelial Core', connections: [2, 3, 4], activity: 0.9 },
    { id: 2, x: 350, y: 80, size: 20, type: 'relay', label: 'Spore Carrier', connections: [1, 5, 6], activity: 0.7 },
    { id: 3, x: 250, y: 200, size: 22, type: 'hub', label: 'Growth Center', connections: [1, 4, 7], activity: 0.8 },
    { id: 4, x: 450, y: 150, size: 18, type: 'endpoint', label: 'Fruiting Body', connections: [1, 3], activity: 0.6 },
    { id: 5, x: 500, y: 250, size: 19, type: 'relay', label: 'Hyphal Bridge', connections: [2, 6], activity: 0.5 },
    { id: 6, x: 600, y: 180, size: 16, type: 'endpoint', label: 'Spore Pod', connections: [2, 5], activity: 0.4 },
    { id: 7, x: 180, y: 320, size: 17, type: 'endpoint', label: 'Root Tip', connections: [3], activity: 0.3 },
    { id: 8, x: 680, y: 220, size: 19, type: 'endpoint', label: 'Spore Cluster', connections: [6, 7], activity: 0.6 }
  ];

  const getConnectionPath = useCallback((from: NetworkNode, to: NetworkNode) => {
    const midX = (from.x + to.x) / 2;
    const midY = (from.y + to.y) / 2;
    const offset = Math.sin((from.x + to.x) / 100) * 25;
    return `M${from.x},${from.y} Q${midX + offset},${midY - offset} ${to.x},${to.y}`;
  }, []);

  const handleNodeClick = useCallback((nodeId: number) => {
    setClickedNode(nodeId);
    setPulseAnimation(nodeId);
    
    // Reset after animation
    setTimeout(() => {
      setClickedNode(null);
      setPulseAnimation(null);
    }, 2000);
  }, []);

  const getNodeColor = (node: NetworkNode, isHovered: boolean, isClicked: boolean) => {
    if (isClicked) return '#FF6B9D';
    if (isHovered) return '#7A5CFF';
    
    switch (node.type) {
      case 'hub': return '#8CFFDA';
      case 'relay': return '#C4B5FD';
      case 'endpoint': return '#A78BFA';
      default: return '#8CFFDA';
    }
  };

  return (
    <div className="relative w-full max-w-5xl mx-auto px-2 sm:px-4 pb-16 sm:pb-20">
      <motion.svg 
        width="100%" 
        height="300" 
        viewBox="0 0 800 300" 
        className="overflow-visible h-48 sm:h-64 md:h-80 lg:h-96"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, ease: 'easeOut' }}
      >
        <defs>
          {/* Enhanced multi-layer glow filters */}
          <filter id="nodeGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          
          <filter id="nodeGlowIntense" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur stdDeviation="12" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
          
          {/* Enhanced connection glow */}
          <filter id="connectionGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>

          {/* Dynamic gradients for different connection types */}
          <linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8CFFDA" stopOpacity="0.4">
              <animate attributeName="stop-opacity" values="0.4;0.9;0.4" dur="2.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="50%" stopColor="#7A5CFF" stopOpacity="0.7">
              <animate attributeName="stop-opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite"/>
            </stop>
            <stop offset="100%" stopColor="#8CFFDA" stopOpacity="0.4">
              <animate attributeName="stop-opacity" values="0.4;0.9;0.4" dur="2.5s" repeatCount="indefinite"/>
            </stop>
          </linearGradient>

          {/* Enhanced spore gradients */}
          <radialGradient id="sporeGradient1">
            <stop offset="0%" stopColor="#8CFFDA" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#8CFFDA" stopOpacity="0.1"/>
          </radialGradient>
          
          <radialGradient id="sporeGradient2">
            <stop offset="0%" stopColor="#7A5CFF" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#7A5CFF" stopOpacity="0.1"/>
          </radialGradient>
          
          <radialGradient id="sporeGradient3">
            <stop offset="0%" stopColor="#FF6B9D" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#FF6B9D" stopOpacity="0.1"/>
          </radialGradient>
        </defs>

        {/* Enhanced background fungal texture with organic patterns */}
        <g opacity="0.08">
          {Array.from({ length: 30 }).map((_, i) => {
            const startX = Math.random() * 800;
            const startY = Math.random() * 400;
            const endX = startX + (Math.random() - 0.5) * 200;
            const endY = startY + (Math.random() - 0.5) * 200;
            const midX = (startX + endX) / 2 + (Math.random() - 0.5) * 100;
            const midY = (startY + endY) / 2 + (Math.random() - 0.5) * 100;
            
            return (
              <path
                key={`bg-${i}`}
                d={`M${startX},${startY} Q${midX},${midY} ${endX},${endY}`}
                stroke={i % 3 === 0 ? '#8CFFDA' : i % 3 === 1 ? '#7A5CFF' : '#C4B5FD'}
                strokeWidth={Math.random() * 1.5 + 0.5}
                fill="none"
                opacity={Math.random() * 0.4 + 0.1}
              >
                <animate 
                  attributeName="opacity" 
                  values={`${Math.random() * 0.2};${Math.random() * 0.5 + 0.2};${Math.random() * 0.2}`}
                  dur={`${Math.random() * 8 + 4}s`}
                  repeatCount="indefinite"
                />
              </path>
            );
          })}
        </g>

        {/* Enhanced floating spores with variety */}
        <g>
          {spores.map((spore, index) => {
            const gradientId = `sporeGradient${(index % 3) + 1}`;
            return (
              <circle
                key={spore.id}
                cx={spore.x}
                cy={spore.y}
                r={Math.sin(spore.life / 15) * spore.size + spore.size}
                fill={`url(#${gradientId})`}
                opacity={Math.sin(spore.life / 25) * 0.4 + 0.4}
                filter="url(#nodeGlow)"
              >
                <animate 
                  attributeName="r" 
                  values={`${spore.size};${spore.size * 1.5};${spore.size}`}
                  dur={`${3 + Math.random() * 2}s`}
                  repeatCount="indefinite"
                />
              </circle>
            );
          })}
        </g>

        {/* Enhanced network connections with dynamic effects */}
        <g>
          {nodes.map(node => {
            return node.connections.map(connectionId => {
              const targetNode = nodes.find(n => n.id === connectionId);
              if (!targetNode) return null;
              
              const isActive = hoveredNode === node.id || hoveredNode === connectionId || clickedNode === node.id || clickedNode === connectionId;
              const isPulsing = pulseAnimation === node.id || pulseAnimation === connectionId;
              
              return (
                <g key={`${node.id}-${connectionId}`}>
                  {/* Main connection line with enhanced styling */}
                  <path
                    d={getConnectionPath(node, targetNode)}
                    stroke={isPulsing ? '#FF6B9D' : 'url(#connectionGradient)'}
                    strokeWidth={isActive ? '4' : '2.5'}
                    fill="none"
                    filter="url(#connectionGlow)"
                    opacity={isActive ? '1' : '0.7'}
                    strokeDasharray={isPulsing ? '10,5' : 'none'}
                  >
                    {isPulsing && (
                      <animate 
                        attributeName="stroke-dashoffset" 
                        values="0;-15" 
                        dur="0.8s" 
                        repeatCount="indefinite"
                      />
                    )}
                  </path>
                  
                  {/* Enhanced digital pulse effects */}
                  <circle r={isActive ? '4' : '3'} fill={isPulsing ? '#FF6B9D' : '#8CFFDA'} opacity="0.9">
                    <animateMotion 
                      dur={isActive ? '2s' : '3.5s'} 
                      repeatCount="indefinite"
                      path={getConnectionPath(node, targetNode)}
                    />
                    <animate 
                      attributeName="opacity" 
                      values="0;1;0" 
                      dur={isActive ? '2s' : '3.5s'} 
                      repeatCount="indefinite"
                    />
                    <animate 
                      attributeName="r" 
                      values={`${isActive ? '4' : '3'};${isActive ? '6' : '5'};${isActive ? '4' : '3'}`} 
                      dur={isActive ? '2s' : '3.5s'} 
                      repeatCount="indefinite"
                    />
                  </circle>
                  
                  {/* Secondary pulse for active connections */}
                  {isActive && (
                    <circle r="2" fill="#FFFFFF" opacity="0.6">
                      <animateMotion 
                        dur="1.5s" 
                        repeatCount="indefinite"
                        path={getConnectionPath(node, targetNode)}
                        begin="0.5s"
                      />
                      <animate 
                        attributeName="opacity" 
                        values="0;0.8;0" 
                        dur="1.5s" 
                        repeatCount="indefinite"
                        begin="0.5s"
                      />
                    </circle>
                  )}
                </g>
              );
            })
          })}
        </g>

        {/* Enhanced network nodes with rich interactions */}
        <g>
          {nodes.map(node => {
            const isHovered = hoveredNode === node.id;
            const isClicked = clickedNode === node.id;
            const isPulsing = pulseAnimation === node.id;
            const nodeColor = getNodeColor(node, isHovered, isClicked);
            
            return (
              <g key={node.id}>
                {/* Outer glow ring for hovered/clicked states */}
                {(isHovered || isClicked) && (
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={node.size + 15}
                    fill="none"
                    stroke={nodeColor}
                    strokeWidth="3"
                    opacity={isClicked ? '0.8' : '0.4'}
                    filter="url(#nodeGlowIntense)"
                  >
                    <animate 
                      attributeName="r" 
                      values={`${node.size + 10};${node.size + 20};${node.size + 10}`} 
                      dur={isClicked ? '1s' : '2s'} 
                      repeatCount="indefinite"
                    />
                    <animate 
                      attributeName="opacity" 
                      values={isClicked ? '0.8;0.4;0.8' : '0.4;0.7;0.4'} 
                      dur={isClicked ? '1s' : '2s'} 
                      repeatCount="indefinite"
                    />
                  </circle>
                )}
                
                {/* Activity indicator ring */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.size + 6}
                  fill="none"
                  stroke={nodeColor}
                  strokeWidth="1.5"
                  opacity={node.activity * 0.6}
                  strokeDasharray={`${node.activity * 20},${(1 - node.activity) * 20}`}
                >
                  <animateTransform 
                    attributeName="transform" 
                    type="rotate" 
                    values={`0 ${node.x} ${node.y};360 ${node.x} ${node.y}`} 
                    dur={`${4 / node.activity}s`} 
                    repeatCount="indefinite"
                  />
                </circle>
                
                {/* Main node with enhanced styling */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.size}
                  fill={nodeColor}
                  stroke="#ffffff"
                  strokeWidth={isHovered ? '3' : '2'}
                  filter={isClicked ? 'url(#nodeGlowIntense)' : 'url(#nodeGlow)'}
                  className="cursor-pointer transition-all duration-300 hover:drop-shadow-2xl"
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => handleNodeClick(node.id)}
                >
                  <animate 
                    attributeName="r" 
                    values={`${node.size};${node.size + (isHovered ? 4 : 2)};${node.size}`} 
                    dur={`${2 + node.id * 0.3}s`} 
                    repeatCount="indefinite"
                  />
                  {isPulsing && (
                    <animate 
                      attributeName="r" 
                      values={`${node.size};${node.size + 8};${node.size}`} 
                      dur="0.6s" 
                      repeatCount="3"
                    />
                  )}
                </circle>
                
                {/* Node type indicator */}
                <text
                  x={node.x}
                  y={node.y + 1}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill={node.type === 'hub' ? '#000' : '#fff'}
                  fontSize={node.size > 18 ? '12' : '10'}
                  fontWeight="bold"
                  className="pointer-events-none select-none"
                >
                  {node.type === 'hub' ? '🌐' : node.type === 'relay' ? '🔄' : '📡'}
                </text>
                
                {/* Node label on hover */}
                {isHovered && (
                  <g>
                    <rect
                      x={node.x - 30}
                      y={node.y - node.size - 25}
                      width="60"
                      height="16"
                      rx="8"
                      fill="rgba(0,0,0,0.9)"
                      stroke={nodeColor}
                      strokeWidth="1"
                    />
                    <text
                      x={node.x}
                      y={node.y - node.size - 15}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill={nodeColor}
                      fontSize="10"
                      fontWeight="bold"
                      className="pointer-events-none select-none"
                    >
                      {node.label}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>

        {/* Enhanced growing branches with organic patterns */}
        <g opacity="0.3">
          {nodes.filter(n => n.type === 'hub').map((node, i) => {
            const branchCount = 3 + i;
            return Array.from({ length: branchCount }).map((_, j) => {
              const angle = (j / branchCount) * Math.PI * 2;
              const length = 60 + Math.random() * 40;
              const endX = node.x + Math.cos(angle) * length;
              const endY = node.y + Math.sin(angle) * length;
              const midX = node.x + Math.cos(angle) * (length * 0.6);
              const midY = node.y + Math.sin(angle) * (length * 0.6) + (Math.random() - 0.5) * 30;
              
              return (
                <g key={`branch-${i}-${j}`}>
                  <path
                    d={`M${node.x},${node.y} Q${midX},${midY} ${endX},${endY}`}
                    stroke={node.type === 'hub' ? '#8CFFDA' : '#7A5CFF'}
                    strokeWidth={Math.random() * 1.5 + 0.5}
                    fill="none"
                    strokeDasharray="8,4"
                    opacity={0.4}
                  >
                    <animate 
                      attributeName="stroke-dashoffset" 
                      values="0;-12" 
                      dur={`${2 + Math.random() * 2}s`} 
                      repeatCount="indefinite"
                    />
                    <animate 
                      attributeName="opacity" 
                      values="0;0.6;0" 
                      dur={`${5 + i + j}s`} 
                      repeatCount="indefinite"
                      begin={`${Math.random() * 2}s`}
                    />
                  </path>
                  
                  {/* Branch endpoint spore */}
                  <circle
                    cx={endX}
                    cy={endY}
                    r="2"
                    fill={node.type === 'hub' ? '#8CFFDA' : '#7A5CFF'}
                    opacity="0.6"
                  >
                    <animate 
                      attributeName="r" 
                      values="1;3;1" 
                      dur={`${3 + Math.random() * 2}s`} 
                      repeatCount="indefinite"
                      begin={`${Math.random() * 3}s`}
                    />
                    <animate 
                      attributeName="opacity" 
                      values="0.2;0.8;0.2" 
                      dur={`${3 + Math.random() * 2}s`} 
                      repeatCount="indefinite"
                      begin={`${Math.random() * 3}s`}
                    />
                  </circle>
                </g>
              );
            });
          })}
        </g>
      </motion.svg>
      
      {/* Enhanced interactive overlay with rich information */}
      <div className="absolute inset-0 pointer-events-none">
        {hoveredNode && !clickedNode && (() => {
          const node = nodes.find(n => n.id === hoveredNode);
          if (!node) return null;
          
          // Calculate tooltip position based on node coordinates
          const tooltipX = (node.x / 800) * 100; // Convert to percentage
          const tooltipY = (node.y / 300) * 100; // Convert to percentage
          
          return (
            <motion.div 
              className="absolute bg-gradient-to-br from-black/95 to-fungal-dark/95 backdrop-blur-md rounded-xl px-3 py-2 sm:px-4 sm:py-3 border border-glow-mint/30 shadow-[0_0_30px_rgba(140,255,218,0.4)] z-50 text-xs sm:text-sm"
              style={{
                left: `${Math.max(10, Math.min(90, tooltipX))}%`,
                top: `${Math.max(5, Math.min(85, tooltipY))}%`,
                transform: tooltipY < 30 ? 'translate(-50%, 25px)' : 'translate(-50%, -100%)',
                minWidth: '140px',
                maxWidth: '200px'
              }}
              initial={{ opacity: 0, y: 10, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
            >
              <div className="text-glow-mint text-lg font-bold mb-1">
                {node.label}
              </div>
              <div className="text-muted-white/80 text-sm mb-2">
                {node.type === 'hub' ? 'MYCELIAL HUB' : 
                 node.type === 'relay' ? 'SPORE RELAY' : 'GROWTH POINT'}
              </div>
              <div className="flex items-center justify-center gap-4 text-xs">
                <span className="text-neural-violet">
                  {node.connections.length} connections
                </span>
                <span className="text-glow-mint">
                  {Math.round(node.activity * 100)}% active
                </span>
              </div>
              
              {/* Activity indicator */}
              <div className="mt-3 w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-glow-mint to-neural-violet rounded-full transition-all duration-500"
                  style={{ width: `${node.activity * 100}%` }}
                />
              </div>
            </motion.div>
          );
        })()}
        
        {clickedNode && (() => {
          const clickedNodeData = nodes.find(n => n.id === clickedNode);
          if (!clickedNodeData) return null;
          
          // Calculate position near the clicked node with better boundary checks
          const nodeX = (clickedNodeData.x / 800) * 100; // Convert to percentage
          const nodeY = (clickedNodeData.y / 300) * 100; // Convert to percentage
          
          // Better boundary checks to prevent overflow - more conservative margins
          const adjustedX = Math.max(20, Math.min(80, nodeX));
          const adjustedY = Math.max(20, Math.min(70, nodeY));
          
          return (
            <div 
              className="absolute pointer-events-none z-40"
              style={{
                left: `${adjustedX}%`,
                top: `${adjustedY}%`,
                transform: 'translate(-50%, -120%)' // Position above the node
              }}
            >
              <motion.div 
                className="bg-gradient-to-br from-neural-violet/95 to-glow-mint/95 backdrop-blur-md rounded-lg px-3 py-2 border border-neural-violet/50 shadow-lg whitespace-nowrap"
                initial={{ opacity: 0, scale: 0.8, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: 10 }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              >
                <div className="text-white text-xs sm:text-sm font-medium flex items-center gap-2">
                  <span className="animate-pulse">🍄</span>
                  <span>Pulse from <span className="font-semibold">{clickedNodeData.label}</span></span>
                </div>
              </motion.div>
            </div>
          );
        })()}
      </div>
      
      {/* Interaction hint - positioned well outside network area */}
      <div className="absolute -bottom-12 sm:-bottom-16 left-1/2 transform -translate-x-1/2 pointer-events-none">
        <motion.div 
          className="text-muted-white/60 text-xs sm:text-sm text-center px-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2, duration: 1 }}
        >
          <div className="mb-1">🍄 <span className="hidden sm:inline">Hover to explore •</span> Tap to pulse</div>
          <div className="text-xs text-muted-white/40 hidden sm:block">Watch the fungal organism respond to your presence</div>
        </motion.div>
      </div>
    </div>
  );
};

export default InteractiveNetwork;
