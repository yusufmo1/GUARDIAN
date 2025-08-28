# GUARDIAN Icon System

GUARDIAN uses [Lucide Icons](https://lucide.dev/) for a comprehensive, professional icon library perfect for pharmaceutical applications.

## Overview

The icon system provides:
- **Full TypeScript Safety** - Complete autocomplete and validation
- **Semantic Sizing** - Standardized size variants (xs, sm, md, lg, xl, 2xl)
- **Accessibility First** - ARIA attributes, focus states, and screen reader support
- **Tree-shakeable** - Only imports icons you actually use (74+ available)
- **Animation Support** - Built-in spin, pulse, and interactive animations
- **Bundle Optimized** - Selective imports with perfect tree-shaking
- **Modern Svelte 5** - Uses runes for optimal performance

## Basic Usage

```svelte
<script>
  import Icon from '$lib/components/common/Icon.svelte';
</script>

<!-- Semantic sizing (recommended) -->
<Icon name="shield" size="md" />
<Icon name="warning" size="lg" color="var(--color-warning-600)" />

<!-- With accessibility -->
<Icon name="loading" size="md" class="spin" aria-label="Processing" />
<Icon name="info" size="sm" title="Additional information" />

<!-- Interactive icons -->
<Icon name="edit" size="sm" class="interactive" />

<!-- Custom numeric sizes still supported -->
<Icon name="heart" size={20} strokeWidth={3} />
```

## Size Variants

```svelte
<!-- Semantic sizes (recommended) -->
<Icon name="home" size="xs" />  <!-- 12px -->
<Icon name="home" size="sm" />  <!-- 16px -->
<Icon name="home" size="md" />  <!-- 20px (default) -->
<Icon name="home" size="lg" />  <!-- 24px -->
<Icon name="home" size="xl" />  <!-- 32px -->
<Icon name="home" size="2xl" /> <!-- 48px -->

<!-- Custom sizes -->
<Icon name="home" size={28} /> <!-- Any number -->
```

## Accessibility Features

```svelte
<!-- Screen reader labels -->
<Icon name="warning" aria-label="Warning: Check protocol compliance" />

<!-- Decorative icons -->
<Icon name="star" aria-hidden={true} />

<!-- Tooltips -->
<Icon name="help" title="Click for help documentation" />

<!-- Interactive focus states -->
<Icon name="edit" class="interactive" tabindex="0" />
```

## Available Icons

### Core Application
- `shield` - Brand/security icon
- `home` - Dashboard/homepage
- `analysis` - Data analysis and charts
- `reports` - Document reports
- `settings` - Configuration and preferences

### File Operations
- `upload` / `download` - File transfer operations
- `file` / `file-text` / `file-image` - Document types
- `save` - Save operations

### Actions & Controls
- `check` / `x` / `close` - Confirmation and dismissal
- `menu` / `search` - Navigation and discovery
- `edit` / `trash` / `copy` - Content manipulation
- `plus` / `minus` - Addition and removal
- `send` - Transmission and communication

### Status & Feedback
- `info` / `warning` / `error` / `success` - Status indicators
- `loading` / `activity` - Progress and activity states

### Navigation
- `arrow-right` / `arrow-left` / `arrow-up` / `arrow-down` - Directional navigation
- `chevron-*` - Subtle directional indicators

### User & Account
- `user` / `user-plus` - User management
- `logout` - Authentication
- `lock` / `unlock` - Security states

### Utility
- `eye` / `eye-off` - Visibility toggles
- `maximize` / `minimize` - Display controls
- `external-link` - External navigation
- `filter` / `sort-asc` / `sort-desc` - Data organization
- `clipboard` / `bookmark` - Content management
- `calendar` / `clock` - Time and scheduling
- `share` / `star` / `heart` - Social actions
- `mail` / `phone` - Communication
- `map-pin` / `globe` - Location and web
- `more-horizontal` / `more-vertical` - Additional options
- `refresh` / `help` - System actions

### Charts & Analytics
- `trending` - Trend visualization
- `users` - User analytics
- `book-open` - Documentation and guides

### Theme & Display
- `sun` / `moon` / `monitor` - Theme selection

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `IconName` | - | Icon name with full TypeScript autocomplete |
| `size` | `IconSize \| number` | `"md"` | Semantic size or custom pixels |
| `color` | `string` | `"currentColor"` | Icon color (inherits by default) |
| `strokeWidth` | `number` | `2` | Stroke thickness |
| `class` | `string` | `""` | Additional CSS classes |
| `aria-label` | `string?` | - | Screen reader description |
| `aria-hidden` | `boolean?` | - | Hide from screen readers |
| `title` | `string?` | - | Tooltip text |

**Type Definitions:**
- `IconName`: All available icon names with autocomplete
- `IconSize`: `"xs" | "sm" | "md" | "lg" | "xl" | "2xl"`

## Animations & Interactions

The icon system supports built-in animations and interactive states:

```svelte
<!-- Spinning loading indicator -->
<Icon name="loading" size="md" class="spin" aria-label="Loading..." />

<!-- Pulsing notification -->
<Icon name="info" size="sm" class="pulse" />

<!-- Interactive button icon -->
<Icon name="edit" size="sm" class="interactive" title="Edit document" />
```

**Available Classes:**
- `spin` - Continuous rotation (perfect for loading states)
- `pulse` - Fade in/out effect (great for notifications)
- `interactive` - Hover effects with scale animation and cursor pointer

## Pharmaceutical-Specific Usage

### Compliance Status Icons
```svelte
<!-- High compliance -->
<Icon name="check" size="sm" color="var(--color-success-600)" aria-label="Compliant" />

<!-- Warning/partial compliance -->
<Icon name="warning" size="sm" color="var(--color-warning-600)" aria-label="Warning" />

<!-- Critical issues -->
<Icon name="error" size="sm" color="var(--color-error-600)" aria-label="Critical issue" />
```

### Document Flow
```svelte
<!-- Upload protocol -->
<Icon name="upload" size="lg" title="Upload document" />

<!-- Processing analysis -->
<Icon name="loading" size="md" class="spin" aria-label="Processing" />

<!-- Download report -->
<Icon name="download" size="md" color="var(--color-primary-600)" title="Download report" />
```

### AI Assistant
```svelte
<!-- Chat interface -->
<Icon name="chat" size="md" title="Open chat" />

<!-- AI activity -->
<Icon name="activity" size="sm" class="pulse" aria-label="AI processing" />

<!-- Helpful information -->
<Icon name="info" size="sm" class="interactive" title="Additional information" />
```

## Custom Styling

Icons inherit color by default but can be customized:

```svelte
<!-- Using CSS custom properties -->
<Icon name="shield" color="var(--color-primary-600)" />

<!-- Direct color values -->
<Icon name="warning" color="#f59e0b" />

<!-- Semantic size variations (recommended) -->
<Icon name="home" size="sm" />  <!-- 16px -->
<Icon name="home" size="md" />  <!-- 20px (default) -->
<Icon name="home" size="lg" />  <!-- 24px -->
<Icon name="home" size="xl" />  <!-- 32px -->

<!-- Custom numeric sizes still supported -->
<Icon name="home" size={28} />  <!-- Any custom size -->
```

## Performance

The icon system is optimized for performance:

- **Tree-shaking**: Only icons actually used are included in the build
- **SVG-based**: Crisp at all resolutions, small file size
- **No runtime overhead**: Icons are compiled at build time

## Migration Complete

The icon system now uses standardized hyphenated naming exclusively:

```svelte
<!-- Use modern hyphenated naming -->
<Icon name="arrow-right" />
<Icon name="arrow-up" />
<Icon name="arrow-down" />
```

**Note**: Legacy underscore naming (`arrow_right`, `arrow_up`, etc.) has been removed. All components now use the modern semantic naming convention.

## Best Practices

1. **Use semantic names**: Choose icons that clearly communicate their function
2. **Consistent sizing**: Use standard sizes (16, 20, 24, 32px) for consistency
3. **Color inheritance**: Let icons inherit color when possible for theme compatibility
4. **Accessibility**: Ensure sufficient contrast for all users
5. **Loading states**: Use spinning icons for loading states
6. **Status indication**: Use color and icon combinations for clear status communication

## Adding New Icons

To add new icons from Lucide:

1. Import the icon component in `Icon.svelte`:
```typescript
import { NewIcon } from 'lucide-svelte';
```

2. Add to the icon mapping:
```typescript
const iconMap = {
  // ... existing icons
  'new-icon': NewIcon,
};
```

3. Update the categories in `constants/index.ts`:
```typescript
export const ICON_CATEGORIES = {
  // ... existing categories
  'New Category': ['new-icon'],
};
```

## Browser Support

The icon system works in all modern browsers that support:
- SVG elements
- CSS transforms (for animations)
- ES6 modules

This includes all browsers supported by SvelteKit.

---

For more information about available icons, visit the [Lucide Icons website](https://lucide.dev/) or check the Settings page in the GUARDIAN application for a complete visual reference.