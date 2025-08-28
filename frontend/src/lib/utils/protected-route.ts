// Temporary stub for protected route - simplified for Svelte 5 migration
export const protectedLoad = async () => {
  // Temporary stub - authentication disabled during migration
  return {};
};

export const protectedLoadWithUser = async () => {
  // Temporary stub - authentication disabled during migration
  return {};
};

export function requireClientAuth(): boolean {
  return true; // Temporary stub
}

export function isRouteProtected(pathname: string): boolean {
  return false; // Temporary stub
}