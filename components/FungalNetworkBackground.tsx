const FungalNetworkBackground = () => {
  return (
    <div className="fixed top-0 left-0 w-full h-full -z-10 overflow-hidden bg-fungal-dark">
      <div className="absolute top-0 left-0 w-full h-full bg-network-animation"></div>
      <style jsx>{`
        .bg-network-animation {
          background-image: radial-gradient(circle at 20% 20%, rgba(140, 255, 218, 0.1) 0%, transparent 30%),
                            radial-gradient(circle at 80% 70%, rgba(122, 92, 255, 0.1) 0%, transparent 30%);
          background-size: 200% 200%;
          animation: move-network 20s linear infinite;
        }

        @keyframes move-network {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }
      `}</style>
    </div>
  );
};

export default FungalNetworkBackground;
