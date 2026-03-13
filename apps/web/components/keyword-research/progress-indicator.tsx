"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, Search, FileText, Users, Network, Calculator, BarChart } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface ProgressStep {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  progress: number;
}

interface ProgressIndicatorProps {
  isActive: boolean;
  currentStep?: string;
  currentProgress?: number;
  depth?: "simple" | "medium" | "deep";
  keyword?: string;
  onComplete?: () => void;
  className?: string;
}

const progressSteps: Record<string, ProgressStep[]> = {
  simple: [
    { id: "search", label: "Searching", description: "Searching Adobe Stock...", icon: Search, progress: 20 },
    { id: "scoring", label: "Calculating", description: "Calculating scores...", icon: Calculator, progress: 80 },
    { id: "complete", label: "Complete", description: "Analysis complete!", icon: Check, progress: 100 },
  ],
  medium: [
    { id: "search", label: "Searching", description: "Searching Adobe Stock...", icon: Search, progress: 10 },
    { id: "assets", label: "Analyzing Assets", description: "Analyzing top 50 assets...", icon: FileText, progress: 30 },
    { id: "contributors", label: "Profiling", description: "Profiling contributors...", icon: Users, progress: 60 },
    { id: "similar", label: "Network", description: "Building market network...", icon: Network, progress: 80 },
    { id: "scoring", label: "Scoring", description: "Calculating scores...", icon: Calculator, progress: 90 },
    { id: "complete", label: "Complete", description: "Analysis complete!", icon: Check, progress: 100 },
  ],
  deep: [
    { id: "search", label: "Searching", description: "Searching Adobe Stock...", icon: Search, progress: 5 },
    { id: "assets", label: "Asset Details", description: "Analyzing 100 asset pages...", icon: FileText, progress: 25 },
    { id: "contributors", label: "Contributors", description: "Deep profiling 20 contributors...", icon: Users, progress: 50 },
    { id: "similar", label: "Similar Assets", description: "Mapping asset network...", icon: Network, progress: 70 },
    { id: "visualizations", label: "Visualizations", description: "Generating charts...", icon: BarChart, progress: 85 },
    { id: "scoring", label: "Scoring", description: "Final calculations...", icon: Calculator, progress: 95 },
    { id: "complete", label: "Complete", description: "Analysis complete!", icon: Check, progress: 100 },
  ],
};

export function ProgressIndicator({
  isActive,
  currentStep = "search",
  currentProgress = 0,
  depth = "medium",
  keyword,
  onComplete,
  className = "",
}: ProgressIndicatorProps) {
  const [simulatedProgress, setSimulatedProgress] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const steps = progressSteps[depth] || progressSteps.medium;

  useEffect(() => {
    if (!isActive) {
      setSimulatedProgress(0);
      setCurrentStepIndex(0);
      return;
    }

    if (currentProgress > 0) {
      setSimulatedProgress(currentProgress);
      const stepIdx = steps.findIndex((s) => s.progress >= currentProgress);
      setCurrentStepIndex(stepIdx >= 0 ? stepIdx : steps.length - 1);
      return;
    }

    const interval = setInterval(() => {
      setSimulatedProgress((prev) => {
        const increment = depth === "deep" ? 0.5 : depth === "medium" ? 1 : 2;
        const next = Math.min(99, prev + increment);
        
        const stepIdx = steps.findIndex((s) => s.progress > next);
        setCurrentStepIndex(stepIdx >= 0 ? stepIdx : steps.length - 1);
        
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, currentProgress, depth, steps]);

  useEffect(() => {
    if (currentProgress >= 100 && onComplete) {
      const timer = setTimeout(onComplete, 500);
      return () => clearTimeout(timer);
    }
  }, [currentProgress, onComplete]);

  if (!isActive) return null;

  const activeStep = steps[currentStepIndex] || steps[0];
  const displayProgress = currentProgress > 0 ? currentProgress : simulatedProgress;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        className={`p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg ${className}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-sm">
              {depth === "deep" ? "Comprehensive" : depth === "medium" ? "Deep" : "Simple"} Analysis
            </h3>
            {keyword && (
              <p className="text-xs text-gray-500">Analyzing &quot;{keyword}&quot;</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <Loader2 className="h-4 w-4 text-purple-500" />
            </motion.div>
            <span className="text-sm font-medium text-purple-600">
              {displayProgress.toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <Progress value={displayProgress} className="h-2" />
        </div>

        {/* Steps */}
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const isCompleted = displayProgress >= step.progress;
            const isCurrent = index === currentStepIndex;
            const Icon = step.icon;

            return (
              <div
                key={step.id}
                className="flex flex-col items-center"
              >
                <motion.div
                  initial={false}
                  animate={{
                    scale: isCurrent ? 1.1 : 1,
                    backgroundColor: isCompleted
                      ? "rgb(139, 92, 246)"
                      : isCurrent
                        ? "rgb(233, 213, 255)"
                        : "rgb(229, 231, 235)",
                  }}
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center mb-1
                    ${isCompleted ? "text-white" : isCurrent ? "text-purple-600" : "text-gray-400"}
                  `}
                >
                  {isCompleted && step.id !== "complete" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </motion.div>
                <span
                  className={`text-[10px] font-medium ${
                    isCurrent ? "text-purple-600" : isCompleted ? "text-gray-700 dark:text-gray-300" : "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Current Step Description */}
        <motion.div
          key={activeStep.id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800"
        >
          <p className="text-xs text-center text-gray-500">
            {activeStep.description}
          </p>
        </motion.div>

        {/* Estimated Time */}
        <div className="mt-2 text-center">
          <p className="text-[10px] text-gray-400">
            Estimated time remaining: {" "}
            {depth === "deep"
              ? `${Math.max(1, Math.ceil((100 - displayProgress) / 7))} minutes`
              : depth === "medium"
                ? `${Math.max(1, Math.ceil((100 - displayProgress) / 25))} minutes`
                : `${Math.max(5, Math.ceil((100 - displayProgress) / 2))} seconds`}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default ProgressIndicator;
