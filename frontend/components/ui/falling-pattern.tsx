'use client';

import type React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

type FallingPatternProps = React.ComponentProps<'div'> & {
  color?: string;
  backgroundColor?: string;
  duration?: number;
  blurIntensity?: string;
  density?: number;
};

export function FallingPattern({
  color = 'var(--primary)',
  backgroundColor = 'var(--background)',
  duration = 150,
  blurIntensity = '1em',
  density = 1,
  className,
}: FallingPatternProps) {
  const generateBackgroundImage = () => {
    const patterns = [
      `radial-gradient(4px 100px at 0px 235px, ${color}, transparent)`,
      `radial-gradient(4px 100px at 300px 235px, ${color}, transparent)`,
      `radial-gradient(1.5px 1.5px at 150px 117.5px, ${color} 100%, transparent 150%)`,
      `radial-gradient(4px 100px at 0px 252px, ${color}, transparent)`,
      `radial-gradient(4px 100px at 300px 252px, ${color}, transparent)`,
      `radial-gradient(1.5px 1.5px at 150px 126px, ${color} 100%, transparent 150%)`,
      `radial-gradient(4px 100px at 0px 150px, ${color}, transparent)`,
      `radial-gradient(4px 100px at 300px 150px, ${color}, transparent)`,
      `radial-gradient(1.5px 1.5px at 150px 75px, ${color} 100%, transparent 150%)`,
      `radial-gradient(4px 100px at 0px 179px, ${color}, transparent)`,
      `radial-gradient(4px 100px at 300px 179px, ${color}, transparent)`,
      `radial-gradient(1.5px 1.5px at 150px 89.5px, ${color} 100%, transparent 150%)`,
      `radial-gradient(4px 100px at 0px 299px, ${color}, transparent)`,
      `radial-gradient(4px 100px at 300px 299px, ${color}, transparent)`,
      `radial-gradient(1.5px 1.5px at 150px 149.5px, ${color} 100%, transparent 150%)`,
    ];
    return patterns.join(', ');
  };

  const backgroundSizes = [
    '300px 235px','300px 235px','300px 235px',
    '300px 252px','300px 252px','300px 252px',
    '300px 150px','300px 150px','300px 150px',
    '300px 179px','300px 179px','300px 179px',
    '300px 299px','300px 299px','300px 299px',
  ].join(', ');

  const startPositions = '0px 220px, 3px 220px, 151.5px 337.5px, 25px 24px, 28px 24px, 176.5px 150px, 50px 16px, 53px 16px, 201.5px 91px, 150px 31px, 153px 31px, 301.5px 120.5px, 175px 235px, 178px 235px, 326.5px 384.5px';
  const endPositions = '0px 6800px, 3px 6800px, 151.5px 6917.5px, 25px 13632px, 28px 13632px, 176.5px 13758px, 50px 5416px, 53px 5416px, 201.5px 5491px, 150px 9876px, 153px 9876px, 301.5px 9965.5px, 175px 13391px, 178px 13391px, 326.5px 13540.5px';

  return (
    <div className={cn('relative h-full w-full p-1', className)}>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
        className="size-full"
      >
        <motion.div
          className="relative size-full z-0"
          style={{
            backgroundColor,
            backgroundImage: generateBackgroundImage(),
            backgroundSize: backgroundSizes,
          }}
          variants={{
            initial: { backgroundPosition: startPositions },
            animate: {
              backgroundPosition: [startPositions, endPositions],
              transition: { duration, ease: 'linear', repeat: Infinity },
            },
          }}
          initial="initial"
          animate="animate"
        />
      </motion.div>
      <div
        className="absolute inset-0 z-1"
        style={{
          backdropFilter: `blur(${blurIntensity})`,
          backgroundImage: `radial-gradient(circle at 50% 50%, transparent 0, transparent 2px, ${backgroundColor} 2px)`,
          backgroundSize: `${8 * density}px ${8 * density}px`,
        }}
      />
    </div>
  );
}
