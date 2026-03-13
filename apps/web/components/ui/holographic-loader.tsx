"use client";

import { motion } from "framer-motion";

interface HolographicLoaderProps {
  progress?: number;
  message?: string;
}

export function HolographicLoader({ progress = 0, message = "Searching..." }: HolographicLoaderProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      {/* Outer glow container */}
      <div className="relative">
        {/* Holographic rings */}
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            background: "conic-gradient(from 0deg, transparent, rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.3), rgba(16, 185, 129, 0.3), transparent)",
            filter: "blur(20px)",
          }}
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
        
        {/* Main loader container */}
        <div className="relative w-40 h-40 flex items-center justify-center">
          {/* Outer ring */}
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-transparent"
            style={{
              background: "linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(59, 130, 246, 0.1)) padding-box, linear-gradient(135deg, #8b5cf6, #3b82f6, #10b981) border-box",
            }}
            animate={{ rotate: -360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          />
          
          {/* Middle ring */}
          <motion.div
            className="absolute inset-4 rounded-full border-2 border-transparent"
            style={{
              background: "linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(16, 185, 129, 0.1)) padding-box, linear-gradient(135deg, #3b82f6, #10b981, #8b5cf6) border-box",
            }}
            animate={{ rotate: 360 }}
            transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
          />
          
          {/* Inner ring */}
          <motion.div
            className="absolute inset-8 rounded-full border-2 border-transparent"
            style={{
              background: "linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(139, 92, 246, 0.1)) padding-box, linear-gradient(135deg, #10b981, #8b5cf6, #3b82f6) border-box",
            }}
            animate={{ rotate: -360 }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
          />
          
          {/* Center orb */}
          <motion.div
            className="relative w-16 h-16 rounded-full flex items-center justify-center"
            style={{
              background: "radial-gradient(circle at 30% 30%, rgba(139, 92, 246, 0.8), rgba(59, 130, 246, 0.6), rgba(16, 185, 129, 0.4))",
              boxShadow: "0 0 40px rgba(139, 92, 246, 0.5), inset 0 0 20px rgba(255, 255, 255, 0.2)",
            }}
            animate={{
              scale: [1, 1.1, 1],
              boxShadow: [
                "0 0 40px rgba(139, 92, 246, 0.5), inset 0 0 20px rgba(255, 255, 255, 0.2)",
                "0 0 60px rgba(59, 130, 246, 0.6), inset 0 0 30px rgba(255, 255, 255, 0.3)",
                "0 0 40px rgba(139, 92, 246, 0.5), inset 0 0 20px rgba(255, 255, 255, 0.2)",
              ],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            {/* Progress text */}
            <span className="text-white font-bold text-lg drop-shadow-lg">
              {Math.round(progress)}%
            </span>
          </motion.div>
          
          {/* Floating particles */}
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full"
              style={{
                background: `linear-gradient(135deg, ${
                  ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"][i]
                }, transparent)`,
                left: "50%",
                top: "50%",
              }}
              animate={{
                x: [0, Math.cos((i * 60 * Math.PI) / 180) * 80, 0],
                y: [0, Math.sin((i * 60 * Math.PI) / 180) * 80, 0],
                opacity: [0, 1, 0],
                scale: [0.5, 1.5, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                delay: i * 0.3,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </div>
      
      {/* Message */}
      <motion.p
        className="mt-8 text-lg font-medium bg-gradient-to-r from-violet-500 via-blue-500 to-emerald-500 bg-clip-text text-transparent"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        {message}
      </motion.p>
      
      {/* Progress bar */}
      <div className="mt-4 w-64 h-2 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{
            background: "linear-gradient(90deg, #8b5cf6, #3b82f6, #10b981)",
          }}
          initial={{ width: "0%" }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
      
      {/* Scanning lines effect */}
      <motion.div
        className="mt-6 text-sm text-muted-foreground font-mono"
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        Scanning Adobe Stock database...
      </motion.div>
    </div>
  );
}
