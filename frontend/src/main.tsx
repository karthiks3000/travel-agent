import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';
import { initAmplify } from './lib/amplify-init';
import { logSetupValidation } from './utils/validateSetup';

// Initialize Amplify before rendering the app
const initializeApp = async () => {
  try {
    await initAmplify();
    
    // Validate setup in development
    if (import.meta.env.DEV) {
      await logSetupValidation();
    }
    
    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <App />
      </StrictMode>
    );
  } catch (error) {
    console.error('Failed to initialize application:', error);
    
    // Render error state
    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Application Initialization Failed
            </h1>
            <p className="text-gray-600 mb-4">
              There was an error initializing the application. Please refresh the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      </StrictMode>
    );
  }
};

initializeApp();
