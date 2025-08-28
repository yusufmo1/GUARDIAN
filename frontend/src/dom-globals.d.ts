// Global DOM type declarations for SvelteKit
// This ensures DOM APIs are properly typed in all contexts

/// <reference types="svelte" />
/// <reference types="@sveltejs/kit" />
/// <reference lib="dom" />
/// <reference lib="dom.iterable" />
/// <reference lib="es2022" />

// Make sure DOM globals are available
declare var window: Window & typeof globalThis;
declare var document: Document;
declare var navigator: Navigator;
declare var location: Location;
declare var localStorage: Storage;
declare var sessionStorage: Storage;
declare var console: Console;