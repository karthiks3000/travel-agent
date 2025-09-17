import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface HoverEffectItem {
  title: string;
  description: string;
  icon?: React.ReactNode;
  link?: string;
}

interface HoverEffectProps {
  items: HoverEffectItem[];
  className?: string;
}

export const HoverEffect: React.FC<HoverEffectProps> = ({ items, className }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <div
      className={cn(
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 py-10',
        className
      )}
    >
      {items.map((item, idx) => (
        <div
          key={idx}
          className="relative group block p-2 h-full w-full"
          onMouseEnter={() => setHoveredIndex(idx)}
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <motion.div
            className="absolute inset-0 h-full w-full bg-gradient-to-r from-blue-500 to-teal-500 rounded-3xl blur-sm opacity-0 group-hover:opacity-75 transition duration-200"
            layoutId={hoveredIndex === idx ? 'hovered-background' : undefined}
          />
          <Card className="rounded-2xl h-full w-full p-6 overflow-hidden bg-white border border-transparent group-hover:border-slate-700 relative z-20">
            <CardContent className="p-0">
              <div className="flex flex-col items-center text-center space-y-4">
                {item.icon && (
                  <div className="text-4xl text-blue-600 group-hover:text-blue-700 transition-colors duration-200">
                    {item.icon}
                  </div>
                )}
                <h3 className="text-xl font-bold text-zinc-800 group-hover:text-zinc-900 transition-colors duration-200">
                  {item.title}
                </h3>
                <p className="text-zinc-600 group-hover:text-zinc-700 transition-colors duration-200 leading-relaxed">
                  {item.description}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      ))}
    </div>
  );
};

// Simple Card component for the hover effect
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-2xl p-6 bg-white shadow-lg hover:shadow-xl transition-shadow duration-200',
        className
      )}
    >
      {children}
    </div>
  );
};

const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => {
  return <div className={cn('', className)}>{children}</div>;
};