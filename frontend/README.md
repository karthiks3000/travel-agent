# Travel Agent Frontend

A React-based frontend interface for the travel agent system built with modern web technologies.

## Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe JavaScript development
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **Aceternity UI** - Modern UI component library
- **React Router v7** - Client-side routing
- **Zustand** - Lightweight state management
- **Framer Motion** - Animation library
- **ESLint + Prettier** - Code linting and formatting

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Linting and Formatting

```bash
# Run ESLint
npm run lint

# Fix ESLint issues
npm run lint:fix

# Check Prettier formatting
npm run format:check

# Format code with Prettier
npm run format

# Type checking
npm run type-check
```

## Project Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Page components
├── stores/             # Zustand state stores
├── utils/              # Utility functions
├── types/              # TypeScript type definitions
└── services/           # API services
```

## Features

- Modern, responsive design with Tailwind CSS
- Type-safe development with TypeScript
- State management with Zustand
- Client-side routing with React Router
- AWS Cognito authentication integration
- Chat interface for travel agent interaction
- Results display for flights, accommodations, and restaurants
- Mobile-responsive design

## Development Guidelines

- Use TypeScript strict mode
- Follow ESLint and Prettier configurations
- Use Tailwind CSS for styling
- Implement components with Aceternity UI
- Use Zustand for global state management
- Follow React best practices and hooks patterns