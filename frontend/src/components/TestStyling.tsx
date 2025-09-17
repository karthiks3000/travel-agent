import React from 'react';
import { motion } from 'framer-motion';
import { ShadcnButton } from './ui/shadcn-button';

export const TestStyling: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Styling Test</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Tailwind Test */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Tailwind CSS</h2>
            <p className="text-gray-600 mb-4">This should be styled with Tailwind CSS.</p>
            <div className="bg-blue-500 text-white px-4 py-2 rounded">Blue Box</div>
          </div>

          {/* Framer Motion Test */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Framer Motion</h2>
            <p className="text-gray-600 mb-4">This should animate in.</p>
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="bg-green-500 text-white px-4 py-2 rounded cursor-pointer"
            >
              Hover me
            </motion.div>
          </motion.div>

          {/* Shadcn Button Test */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">Shadcn Button</h2>
            <div className="space-y-4">
              <ShadcnButton>Default Button</ShadcnButton>
              <ShadcnButton variant="outline">Outline Button</ShadcnButton>
              <ShadcnButton variant="secondary">Secondary Button</ShadcnButton>
            </div>
          </div>

          {/* CSS Variables Test */}
          <div className="bg-card text-card-foreground rounded-lg shadow-lg p-6 border">
            <h2 className="text-2xl font-semibold mb-4">CSS Variables</h2>
            <p className="text-muted-foreground mb-4">This uses CSS variables from shadcn.</p>
            <div className="bg-primary text-primary-foreground px-4 py-2 rounded">
              Primary Color
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};