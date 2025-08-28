import type { PageLoad } from './$types';
import { browser } from '$app/environment';
import { redirect } from '@sveltejs/kit';
import { authState } from '$lib/stores';

export const load: PageLoad = async ({ url }) => {
  // Only check authentication on the client side
  if (browser) {
    const authenticated = authState.authenticated;
    
    if (!authenticated) {
      console.log('Account page load: Not authenticated, redirecting to login');
      throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
    }
  }
  
  // Return empty data - the component will handle loading user data
  return {};
};