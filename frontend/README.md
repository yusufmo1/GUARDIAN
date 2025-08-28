# GUARDIAN Frontend

> **Guided Universal Adherence & Regulatory Document Intelligence Network**  
> Modern SvelteKit frontend for pharmaceutical protocol compliance analysis

## Technology Stack
- **SvelteKit 2.x** - Full-stack framework with TypeScript
- **Vite** - Fast build tool and development server  
- **TypeScript** - Type-safe development
- **Lucide Icons** - Professional icon system
- **CSS Custom Properties** - Design system implementation

## Overview

The GUARDIAN frontend is a sophisticated web application built with SvelteKit that provides an intuitive interface for pharmaceutical protocol compliance analysis. It offers real-time document processing, AI-powered compliance checking against global regulatory standards, and comprehensive reporting capabilities.

### Key Features

- **Protocol Analysis**: Upload and analyze pharmaceutical protocols against regulatory standards
- **Real-time Processing**: Live status updates during document processing and analysis
- **AI Integration**: Interactive chat interface with compliance guidance
- **Visual Analytics**: Compliance scoring with interactive charts and insights
- **Comprehensive Reports**: PDF generation with detailed findings and recommendations
- **Professional UI**: Clean, accessible interface with pharmaceutical industry aesthetics
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Performance**: Static site generation with optimal loading speeds

## Quick Start

### Prerequisites

- **Node.js** (v18.0.0 or higher)
- **npm** (v9.0.0 or higher)
- **GUARDIAN Backend** running on `http://127.0.0.1:5051` (see backend documentation)

### Installation

```bash
# Navigate to frontend directory
cd guardian/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3001` (or next available port).

### Environment Setup

The frontend automatically proxies API requests to `http://localhost:5000` in development mode. For production deployment, configure the API URL in the settings page or environment variables.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build production-ready static site |
| `npm run preview` | Preview production build locally |
| `npm run check` | Run TypeScript type checking |
| `npm run check:watch` | Run type checking in watch mode |
| `npm run lint` | Run ESLint (if configured) |

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── analysis/        # Compliance analysis components
│   │   │   ├── chat/           # AI chat interface components
│   │   │   ├── common/         # Shared UI components (Button, Card, etc.)
│   │   │   └── upload/         # Document upload components
│   │   ├── constants/          # Application constants and configuration
│   │   ├── services/           # API client and external integrations
│   │   ├── stores/             # Svelte state management
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Utility functions
│   ├── routes/                 # File-based routing (SvelteKit)
│   │   ├── analysis/           # Protocol analysis page
│   │   ├── reports/            # Compliance reports page
│   │   ├── settings/           # Configuration page
│   │   └── +page.svelte        # Dashboard (home page)
│   ├── app.html               # Main HTML template
│   ├── app.css                # Global styles and design system
│   └── app.d.ts               # TypeScript app declarations
├── static/                    # Static assets
├── package.json              # Dependencies and scripts
├── svelte.config.js          # SvelteKit configuration
├── tsconfig.json             # TypeScript configuration
├── vite.config.js            # Vite build configuration
└── README.md                 # This file
```

## Design System

### Colors & Theming

The application uses a comprehensive design system with CSS custom properties:

```css
/* Primary palette */
--color-primary-50: #eff6ff;
--color-primary-500: #3b82f6;
--color-primary-600: #2563eb;

/* Status colors */
--color-success-600: #16a34a;
--color-warning-600: #d97706;
--color-error-600: #dc2626;
```

### Typography

- **Font Stack**: System fonts for optimal performance
- **Scale**: Modular scale from xs (12px) to 4xl (36px)
- **Weights**: 400 (normal), 500 (medium), 600 (semibold), 700 (bold)

### Spacing & Layout

- **Spacing Scale**: 1-20 with 4px base unit
- **Responsive Breakpoints**: Mobile-first approach with tablet and desktop variants
- **Max Widths**: Content containers from sm (640px) to 7xl (1280px)

## Component Architecture

### Core Components (`lib/components/common/`)

| Component | Purpose |
|-----------|---------|
| `Button.svelte` | Consistent button styling with variants |
| `Card.svelte` | Content containers with elevation |
| `Icon.svelte` | Lucide icon system integration |
| `Navigation.svelte` | Application navigation bar |
| `ErrorBoundary.svelte` | Error handling and display |

### Feature Components

- **Analysis Components**: Protocol compliance analysis interface
- **Upload Components**: Document upload with progress tracking
- **Chat Components**: AI-powered compliance assistance
- **Visualization**: Charts and compliance scoring displays

### Icon System

The application uses [Lucide Icons](https://lucide.dev/) with a custom wrapper component providing full TypeScript safety, accessibility, and semantic sizing:

```svelte
<!-- Standard usage with semantic sizes -->
<Icon name="shield" size="lg" color="var(--color-primary-600)" />

<!-- With accessibility -->
<Icon name="loading" size="md" class="spin" aria-label="Processing" />

<!-- Interactive icons -->
<Icon name="edit" size="sm" class="interactive" title="Edit document" />
```

**Size Variants**: `xs` (12px), `sm` (16px), `md` (20px), `lg` (24px), `xl` (32px), `2xl` (48px), or custom number

**Available Categories**:
- Core Application: shield, home, analysis, reports, settings
- File Operations: upload, download, file, file-text, file-image
- Actions: check, x, search, edit, save, send, trash, copy
- Status: info, warning, error, success, loading, activity
- Navigation: arrow-right, arrow-left, chevron-down, chevron-up
- User & Auth: user, logout, lock, unlock
- Utility: refresh, help, more-horizontal, filter, calendar

**Features**:
- ✅ Full TypeScript autocomplete and validation
- ✅ Accessibility with ARIA attributes and focus states
- ✅ Animation support (`spin`, `pulse`, `interactive`)
- ✅ Bundle optimization with tree-shaking
- ✅ Semantic naming with fallback handling

## API Integration

### API Client (`lib/services/api.ts`)

The application includes a comprehensive API client with:

- **Type-safe requests/responses** using TypeScript
- **Error handling** with custom error classes
- **Request/response interceptors**
- **File upload support** with progress tracking
- **WebSocket integration** for real-time updates

### Endpoint Categories

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| **Health** | `/health`, `/health/detailed` | System status monitoring |
| **Documents** | `/api/documents/*` | Document management |
| **Analysis** | `/api/analyze/*` | Protocol analysis |
| **Search** | `/api/search/*` | Vector similarity search |
| **Reports** | `/api/reports/*` | Report generation |

### Usage Example

```typescript
import { documents } from '$lib/services/api';

// Upload document
const response = await documents.upload(file, {
  documentType: 'protocol',
  processImmediately: true
});

// Get analysis results
const analysis = await analysis.get(analysisId);
```

## State Management

### Svelte Stores

The application uses reactive Svelte stores for state management:

| Store | Purpose |
|-------|---------|
| `appStore` | Global application state and settings |
| `documentStore` | Document management and upload progress |
| `analysisStore` | Analysis results and compliance data |
| `chatStore` | Chat interface state |
| `toastStore` | Notification system |

### Store Pattern

```typescript
// Creating a store
const { subscribe, set, update } = writable<StateType>(initialState);

// Reactive updates
$: derivedValue = $store.someProperty;

// Store actions
export const storeActions = {
  updateSetting: (key: string, value: any) => 
    update(state => ({ ...state, [key]: value }))
};
```

## Key Features Deep Dive

### 1. Document Upload & Processing

- **Multi-file support** with drag-and-drop interface
- **File validation** (PDF, TXT, DOCX)
- **Real-time progress tracking** with status updates
- **Error handling** with retry capabilities
- **Base64 encoding** for API compatibility

### 2. Protocol Analysis

- **Global regulatory standards compliance checking**
- **Interactive analysis interface** with customizable options
- **Real-time status polling** during processing
- **Compliance scoring** with visual indicators
- **Detailed findings** with severity classification

### 3. AI Chat Interface

- **Context-aware conversations** about compliance
- **Real-time responses** from LLM integration
- **Message history** with conversation management
- **Typing indicators** and status updates

### 4. Reporting System

- **PDF report generation** with professional formatting
- **Multiple export formats** (PDF, HTML, JSON)
- **Visual analytics** with charts and graphs
- **Compliance summaries** with actionable recommendations

### 5. System Status Monitoring

- **Real-time backend health checking**
- **API connectivity testing**
- **Document statistics** and processing metrics
- **Integration status** for all services

## Development Workflow

### Code Organization

- **Feature-based structure** for scalability
- **TypeScript everywhere** for type safety
- **Component composition** over inheritance
- **Reactive patterns** with Svelte stores

### Best Practices

1. **Component Design**:
   - Single responsibility principle
   - Props typing with TypeScript
   - Event emission for parent communication
   - Consistent styling with design system

2. **State Management**:
   - Centralized stores for shared state
   - Local state for component-specific data
   - Reactive derived values
   - Immutable updates

3. **API Integration**:
   - Type-safe requests/responses
   - Comprehensive error handling
   - Loading states and user feedback
   - Request deduplication where appropriate

### Development Workflow

- **Hot Reload**: Instant updates during development with Vite HMR
- **Type Checking**: Real-time TypeScript validation in VS Code
- **Component Isolation**: Each component is self-contained with scoped styles
- **State Management**: Centralized stores with reactive updates

## Deployment

### Production Build

```bash
# Build static site
npm run build

# Preview production build
npm run preview
```

### Static Deployment

The application builds to a static site using `@sveltejs/adapter-static`:

```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: null
    })
  }
};
```

### Deployment Targets

- **Netlify**: Zero-config deployment with drag-and-drop
- **Vercel**: Automatic deployments from Git
- **GitHub Pages**: Static hosting with Actions
- **AWS S3**: Static website hosting
- **Nginx**: Traditional web server deployment

### Environment Configuration

For production deployment, configure:

1. **API URL**: Set backend API endpoint in settings
2. **CORS**: Ensure backend allows frontend domain
3. **SSL**: Use HTTPS for production deployments
4. **CDN**: Consider CDN for static assets

## Security & Best Practices

- **Input Validation**: All user inputs are validated before API calls
- **XSS Prevention**: Svelte automatically escapes content to prevent XSS
- **API Security**: No sensitive data stored in frontend code
- **Error Handling**: Structured error responses without exposing internals
- **Type Safety**: TypeScript prevents many runtime errors

## Browser Support

- **Modern browsers** (Chrome, Firefox, Safari, Edge)
- **ES2020+ features** with Vite polyfills
- **Progressive enhancement** for older browsers
- **Mobile optimization** with responsive design

## Development Notes

### Project Architecture

This frontend follows a **component-based architecture** with:
- **Feature-based organization** for scalability
- **TypeScript everywhere** for type safety  
- **Reactive state management** with Svelte stores
- **API-first design** with comprehensive backend integration

### Code Patterns Used

```svelte
<!-- Standard Component Pattern -->
<script lang="ts">
  // Props with TypeScript
  export let data: DataType;
  
  // Local reactive state
  let loading = false;
  
  // Reactive statements
  $: processedData = data.map(transform);
  
  // Event handlers
  function handleAction() {
    // Logic here
  }
</script>

<div class="component">
  {#if loading}
    <Icon name="loading" class="spin" />
  {:else}
    <!-- Content -->
  {/if}
</div>

<style>
  .component {
    /* Design system variables */
    padding: var(--space-4);
    background: var(--color-surface);
  }
</style>
```

### Key Implementation Details

- **Static Site Generation**: Uses `@sveltejs/adapter-static` for optimal performance
- **API Proxy**: Development server proxies `/api` to `http://localhost:5000` 
- **Real-time Updates**: WebSocket integration for live status updates
- **File Upload**: Base64 encoding for API compatibility with progress tracking
- **Error Boundaries**: Comprehensive error handling with user-friendly messages

## Technical References

- [SvelteKit Documentation](https://kit.svelte.dev/docs) - Framework reference
- [TypeScript Handbook](https://www.typescriptlang.org/docs/) - Type system
- [Vite Configuration](https://vitejs.dev/guide/) - Build tool setup
- [Lucide Icons](https://lucide.dev/) - Icon system reference

---

*Personal development reference for GUARDIAN pharmaceutical compliance system*