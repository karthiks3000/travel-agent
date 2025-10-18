import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

// Feature icons using simple SVGs
const FlightIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
  </svg>
);

const HotelIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M7 13c1.66 0 3-1.34 3-3S8.66 7 7 7s-3 1.34-3 3 1.34 3 3 3zm12-6h-8v7H3V6H1v15h2v-3h18v3h2v-9c0-2.21-1.79-4-4-4z"/>
  </svg>
);

const RestaurantIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M8.1 13.34l2.83-2.83L3.91 3.5c-1.56 1.56-1.56 4.09 0 5.66l4.19 4.18zm6.78-1.81c1.53.71 3.68.21 5.27-1.38 1.91-1.91 2.28-4.65.81-6.12-1.46-1.46-4.20-1.10-6.12.81-1.59 1.59-2.09 3.74-1.38 5.27L3.7 19.87l1.41 1.41L12 14.41l6.88 6.88 1.41-1.41L13.41 13l1.47-1.47z"/>
  </svg>
);

const ItineraryIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M9 11H7v6h2v-6zm4 0h-2v6h2v-6zm4 0h-2v6h2v-6zm2.5-5H19V4h-2v2H7V4H5v2H4.5C3.67 6 3 6.67 3 7.5v11C3 19.33 3.67 20 4.5 20h15c.83 0 1.5-.67 1.5-1.5v-11C21 6.67 20.33 6 19.5 6z"/>
  </svg>
);

const AIIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
  </svg>
);

const SupportIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.5 6L12 10.5 8.5 8 12 5.5 15.5 8zM8.5 16L12 13.5 15.5 16 12 18.5 8.5 16z"/>
  </svg>
);

const features = [
  {
    title: "Smart Flight Search",
    description: "Find the best flights with AI-powered search that considers your preferences, budget, and travel patterns to deliver personalized results.",
    icon: <FlightIcon />,
  },
  {
    title: "Perfect Accommodations",
    description: "Discover hotels, Airbnbs, and unique stays that match your style and budget, with detailed insights and honest reviews.",
    icon: <HotelIcon />,
  },
  {
    title: "Local Dining Experiences",
    description: "Explore authentic restaurants and hidden culinary gems recommended by locals and fellow travelers.",
    icon: <RestaurantIcon />,
  },
  {
    title: "Intelligent Itinerary Planning",
    description: "Create seamless travel plans that optimize your time, minimize travel between locations, and maximize your experiences.",
    icon: <ItineraryIcon />,
  },
  {
    title: "AI-Powered Recommendations",
    description: "Get personalized suggestions based on your travel history, preferences, and real-time data from millions of travelers.",
    icon: <AIIcon />,
  },
  {
    title: "24/7 Travel Support",
    description: "Access instant help and support throughout your journey with our AI assistant that never sleeps.",
    icon: <SupportIcon />,
  },
];

// Custom Hover Effect component with light theme
const CustomHoverEffect = ({
  items,
  className,
}: {
  items: typeof features;
  className?: string;
}) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 py-10",
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
          <AnimatePresence>
            {hoveredIndex === idx && (
              <motion.span
                className="absolute inset-0 h-full w-full bg-gradient-to-r from-blue-50 to-indigo-50 block rounded-3xl"
                layoutId="hoverBackground"
                initial={{ opacity: 0 }}
                animate={{
                  opacity: 1,
                  transition: { duration: 0.15 },
                }}
                exit={{
                  opacity: 0,
                  transition: { duration: 0.15, delay: 0.2 },
                }}
              />
            )}
          </AnimatePresence>
          <div className="rounded-2xl h-full w-full p-6 overflow-hidden bg-white border border-gray-100 group-hover:border-blue-200 relative z-20 shadow-sm hover:shadow-lg transition-shadow duration-300">
            <div className="relative z-50">
              <div className="flex flex-col items-center text-center space-y-4">
                <div className="text-blue-600 group-hover:text-blue-700 transition-colors duration-200">
                  {item.icon}
                </div>
                <h4 className="text-gray-900 font-bold tracking-wide text-lg">
                  {item.title}
                </h4>
                <p className="text-gray-600 tracking-wide leading-relaxed text-sm">
                  {item.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export const FeaturesGrid: React.FC = () => {
  return (
    <section id="features" className="py-20 px-4 bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-6">
            Everything You Need for
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
              {" "}Perfect Travel
            </span>
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Our AI-powered travel agent combines cutting-edge technology with personalized service 
            to make your travel planning effortless and enjoyable.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
          className="max-w-6xl mx-auto"
        >
          <CustomHoverEffect items={features} />
        </motion.div>

        {/* Additional visual elements */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <div className="inline-flex items-center space-x-2 bg-blue-50 px-6 py-3 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700">
              Trusted by 10,000+ travelers worldwide
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
