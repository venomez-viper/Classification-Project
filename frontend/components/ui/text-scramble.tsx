'use client';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { motion, MotionProps } from 'framer-motion';

type TextScrambleProps = {
  children: string;
  duration?: number;
  speed?: number;
  characterSet?: string;
  as?: React.ElementType;
  className?: string;
  trigger?: boolean;
  onScrambleComplete?: () => void;
} & MotionProps;

const defaultChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const motionComponents = {
  div: motion.div,
  h1: motion.h1,
  h2: motion.h2,
  h3: motion.h3,
  p: motion.p,
  span: motion.span,
};

export function TextScramble({
  children,
  duration = 0.8,
  speed = 0.04,
  characterSet = defaultChars,
  className,
  as: Component = 'p',
  trigger = true,
  onScrambleComplete,
  ...props
}: TextScrambleProps) {
  const MotionComponent = motionComponents[Component as keyof typeof motionComponents] ?? motion.p;
  const [displayText, setDisplayText] = useState(children);

  // Use refs to avoid stale closure issues and prevent infinite re-triggering
  const isAnimatingRef = useRef(false);
  const hasAnimatedRef = useRef(false);
  const completeRef = useRef(onScrambleComplete);
  const childrenRef = useRef(children);
  const chars = useMemo(() => characterSet.split(''), [characterSet]);

  useEffect(() => {
    completeRef.current = onScrambleComplete;
  }, [onScrambleComplete]);

  useEffect(() => {
    childrenRef.current = children;
    setDisplayText(children);
  }, [children]);

  const scramble = useCallback(() => {
    // Guard: only run once - never re-run while animating or after completion
    if (isAnimatingRef.current || hasAnimatedRef.current) return;
    isAnimatingRef.current = true;
    hasAnimatedRef.current = true;

    const target = childrenRef.current;
    const steps = duration / speed;
    let step = 0;

    const interval = setInterval(() => {
      let scrambled = '';
      const progress = step / steps;
      for (let i = 0; i < target.length; i++) {
        if (target[i] === ' ') { scrambled += ' '; continue; }
        if (progress * target.length > i) {
          scrambled += target[i];
        } else {
          scrambled += chars[Math.floor(Math.random() * chars.length)];
        }
      }
      setDisplayText(scrambled);
      step++;
      if (step > steps) {
        clearInterval(interval);
        setDisplayText(target);
        isAnimatingRef.current = false;
        completeRef.current?.();
      }
    }, speed * 1000);

    return () => clearInterval(interval);
  // Stable deps only - intentionally excludes isAnimating to avoid re-creation loop
  }, [chars, duration, speed]);

  // Fire only once when trigger first becomes true
  useEffect(() => {
    if (!trigger) return;
    const timer = window.setTimeout(scramble, 100);
    return () => window.clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]); // intentionally omit `scramble` from deps - it must not re-trigger on callback recreation

  return (
    <MotionComponent className={className} {...props}>
      {displayText}
    </MotionComponent>
  );
}
