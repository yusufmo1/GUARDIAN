<script lang="ts">
  // Import global icon styles
  import '$lib/styles/icon.css';
  
  // Lucide Icon imports
  import {
    Shield,
    Home,
    BarChart3,
    FileText,
    Settings,
    Upload,
    Download,
    File,
    Check,
    X,
    Menu,
    Search,
    MessageCircle,
    Info,
    AlertTriangle,
    AlertCircle,
    Loader2,
    ArrowRight,
    ArrowLeft,
    ArrowUp,
    ArrowDown,
    CheckCircle,
    XCircle,
    CloudUpload,
    FileImage,
    Activity,
    TrendingUp,
    Users,
    BookOpen,
    Clipboard,
    Eye,
    EyeOff,
    RefreshCw,
    Plus,
    Minus,
    Edit,
    Trash2,
    Copy,
    ExternalLink,
    Calendar,
    Clock,
    Star,
    Heart,
    Bookmark,
    Share,
    Filter,
    SortAsc,
    SortDesc,
    MoreHorizontal,
    MoreVertical,
    ChevronDown,
    ChevronUp,
    ChevronLeft,
    ChevronRight,
    Maximize,
    Minimize,
    Save,
    Send,
    Mail,
    Phone,
    MapPin,
    Globe,
    Lock,
    Unlock,
    User,
    UserPlus,
    LogOut,
    HelpCircle,
    Sun,
    Moon,
    Monitor,
    type Icon as LucideIcon
  } from 'lucide-svelte';

  // Icon size variants for consistency
  const ICON_SIZES = {
    xs: 12,
    sm: 16,
    md: 20,
    lg: 24,
    xl: 32,
    '2xl': 48
  } as const;
  
  type IconSize = keyof typeof ICON_SIZES | number;

  // Icon mapping for backward compatibility and semantic naming
  const iconMap = {
    // Core application icons
    shield: Shield,
    home: Home,
    analysis: BarChart3,
    reports: FileText,
    settings: Settings,
    
    // File operations
    upload: CloudUpload,
    download: Download,
    file: File,
    'file-text': FileText,
    'file-image': FileImage,
    
    // Actions
    check: Check,
    x: X,
    close: X,
    menu: Menu,
    search: Search,
    chat: MessageCircle,
    
    // Status & feedback
    info: Info,
    warning: AlertTriangle,
    error: AlertCircle,
    success: CheckCircle,
    loading: Loader2,
    loader: Loader2,  // Alias for loading
    activity: Activity,
    
    // Navigation
    'arrow-right': ArrowRight,
    'arrow-left': ArrowLeft,
    'arrow-up': ArrowUp,
    'arrow-down': ArrowDown,
    'chevron-down': ChevronDown,
    'chevron-up': ChevronUp,
    'chevron-left': ChevronLeft,
    'chevron-right': ChevronRight,
    
    // Content & editing
    edit: Edit,
    trash: Trash2,
    copy: Copy,
    save: Save,
    send: Send,
    plus: Plus,
    minus: Minus,
    
    // Visibility & display
    eye: Eye,
    'eye-off': EyeOff,
    maximize: Maximize,
    minimize: Minimize,
    'external-link': ExternalLink,
    
    // Data & organization
    filter: Filter,
    'sort-asc': SortAsc,
    'sort-desc': SortDesc,
    clipboard: Clipboard,
    bookmark: Bookmark,
    
    // Time & calendar
    calendar: Calendar,
    clock: Clock,
    
    // Social & sharing
    share: Share,
    star: Star,
    heart: Heart,
    
    // User & account
    user: User,
    'user-plus': UserPlus,
    login: User, // Use User icon for login
    logout: LogOut,
    lock: Lock,
    unlock: Unlock,
    
    // Communication
    mail: Mail,
    phone: Phone,
    
    // Location & navigation
    'map-pin': MapPin,
    globe: Globe,
    
    // Utility
    'more-horizontal': MoreHorizontal,
    'more-vertical': MoreVertical,
    refresh: RefreshCw,
    help: HelpCircle,
    
    // Charts & analytics (pharmaceutical specific)
    trending: TrendingUp,
    users: Users,
    'book-open': BookOpen,
    
    // Theme & display
    sun: Sun,
    moon: Moon,
    monitor: Monitor,
    
  } as const satisfies Record<string, LucideIcon>;

  // Define types after iconMap is created
  type IconName = keyof typeof iconMap;
  
  interface Props {
    name: IconName;
    size?: IconSize;
    color?: string;
    strokeWidth?: number;
    class?: string;
    'aria-label'?: string;
    'aria-hidden'?: boolean;
    title?: string;
  }

  let { 
    name,
    size = 'md',
    color = 'currentColor',
    strokeWidth = 2,
    class: className = '',
    'aria-label': ariaLabel,
    'aria-hidden': ariaHidden,
    title
  }: Props = $props();

  // Compute resolved size - only reactive when size changes
  const resolvedSize = $derived(typeof size === 'number' ? size : ICON_SIZES[size]);
  
  // Static props object - no need for reactivity here
  const iconProps = {
    get size() { return resolvedSize; },
    color,
    'stroke-width': strokeWidth,
    class: `icon ${className}`.trim(),
    role: ariaHidden ? 'presentation' : 'img',
    'aria-label': ariaLabel,
    'aria-hidden': ariaHidden,
    title
  };

  // Warn about missing icons in development using $effect
  $effect(() => {
    if (typeof window !== 'undefined' && !iconMap[name]) {
      console.warn(`Icon "${name}" not found. Using fallback icon.`);
    }
  });
</script>

<!-- Semantic wrapper with proper accessibility -->
{#if iconMap[name]}
  {@const Component = iconMap[name]}
  <Component {...iconProps} />
{:else}
  <Info {...iconProps} />
{/if}