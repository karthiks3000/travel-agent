import React from 'react';
import { motion } from 'framer-motion';
import { HeroParallax } from '@/components/ui/hero-parallax';
import { TextGenerateEffect } from '@/components/ui/text-generate-effect';

const products = [
  {
    title: "Flight Search",
    link: "#flight-search",
    thumbnail: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500&h=300&fit=crop",
  },
  {
    title: "Hotel Booking",
    link: "#hotel-booking",
    thumbnail: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&h=300&fit=crop",
  },
  {
    title: "Restaurant Finder",
    link: "#restaurant-finder",
    thumbnail: "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=500&h=300&fit=crop",
  },
  {
    title: "Itinerary Planning",
    link: "#itinerary-planning",
    thumbnail: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=500&h=300&fit=crop",
  },
  {
    title: "Local Experiences",
    link: "#local-experiences",
    thumbnail: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=500&h=300&fit=crop",
  },
  {
    title: "Travel Insights",
    link: "#travel-insights",
    thumbnail: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=300&fit=crop",
  },
  {
    title: "Smart Recommendations",
    link: "#smart-recommendations",
    thumbnail: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=500&h=300&fit=crop",
  },
  {
    title: "Travel Support",
    link: "#travel-support",
    thumbnail: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=500&h=300&fit=crop",
  },
  {
    title: "Trip Planning",
    link: "#trip-planning",
    thumbnail: "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=500&h=300&fit=crop",
  },
  {
    title: "Destination Guide",
    link: "#destination-guide",
    thumbnail: "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=500&h=300&fit=crop",
  },
  {
    title: "Budget Tracking",
    link: "#budget-tracking",
    thumbnail: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500&h=300&fit=crop",
  },
  {
    title: "Travel Community",
    link: "#travel-community",
    thumbnail: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=500&h=300&fit=crop",
  },
  {
    title: "Weather Updates",
    link: "#weather-updates",
    thumbnail: "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=500&h=300&fit=crop",
  },
  {
    title: "Currency Exchange",
    link: "#currency-exchange",
    thumbnail: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=500&h=300&fit=crop",
  },
  {
    title: "Travel Insurance",
    link: "#travel-insurance",
    thumbnail: "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=500&h=300&fit=crop",
  },
];

// Custom Header component for our hero section
const CustomHeader = () => {
  return (
    <div className="max-w-7xl relative mx-auto py-20 md:py-40 px-4 w-full left-0 top-0">
      <TextGenerateEffect 
        words="Your AI-Powered Travel Companion Awaits"
        className="text-2xl md:text-7xl font-bold text-gray-900 dark:text-white"
      />
      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="max-w-2xl text-base md:text-xl mt-8 text-gray-600 dark:text-neutral-200"
      >
        Discover, plan, and book your perfect trip with our intelligent travel agent that understands your preferences and finds the best deals across flights, hotels, and experiences.
      </motion.p>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.8 }}
        className="flex flex-col sm:flex-row gap-4 mt-8"
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-8 rounded-lg transition-all duration-300 shadow-lg hover:shadow-xl"
        >
          Start Planning Your Trip
        </motion.button>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="border-2 border-gray-300 hover:border-gray-400 text-gray-700 hover:text-gray-900 font-semibold py-3 px-8 rounded-lg transition-all duration-300 bg-white/80 backdrop-blur-sm"
        >
          Learn More
        </motion.button>
      </motion.div>
    </div>
  );
};

export const HeroSection: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <HeroParallax products={products}>
        <CustomHeader />
      </HeroParallax>
    </div>
  );
};