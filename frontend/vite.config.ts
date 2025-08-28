import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import fs from 'fs';
import path from 'path';

// Svelte 5 compatibility plugin to fix infinite loops
const svelte5CompatPlugin = () => {
	return {
		name: 'svelte-5-compat',
		configureServer(server) {
			// Watch for changes to root.svelte
			server.watcher.on('change', (file) => {
				if (file.endsWith('.svelte-kit/generated/root.svelte')) {
					setTimeout(() => patchRootSvelte(), 100);
				}
			});
			// Initial patch
			setTimeout(() => patchRootSvelte(), 1000);
		},
		buildStart() {
			// Patch during build
			setTimeout(() => patchRootSvelte(), 1000);
		}
	};
};

function patchRootSvelte() {
	const rootPath = path.resolve('.svelte-kit/generated/root.svelte');
	if (!fs.existsSync(rootPath)) return;
	
	let content = fs.readFileSync(rootPath, 'utf-8');
	const original = content;
	
	// Fix the problematic effect that causes infinite loops
	content = content.replace(
		/\$effect\(\(\) => \{\n\t\tstores;page;constructors;components;form;data_0;data_1;\n\t\tstores\.page\.notify\(\);\n\t\}\);/,
		`$effect(() => {
		// Track dependencies
		stores;page;constructors;components;form;data_0;data_1;
		// Defer notify to prevent infinite loops
		if (browser) {
			queueMicrotask(() => stores.page.notify());
		}
	});`
	);
	
	if (content !== original) {
		fs.writeFileSync(rootPath, content);
		console.log('✅ Patched root.svelte for Svelte 5 compatibility');
	}
}

export default defineConfig({
	plugins: [sveltekit(), svelte5CompatPlugin()],
	server: {
		port: 3000,
		proxy: {
			'/api': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/google': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/validate': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/user': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/logout': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/refresh': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/sessions': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/auth/health': {
				target: 'http://localhost:5051',
				changeOrigin: true
			},
			'/docs': {
				target: 'http://localhost:5051',
				changeOrigin: true
			}
		}
	},
	build: {
		rollupOptions: {
			output: {
				manualChunks: {
					'plotly': ['plotly.js-dist-min']
				}
			}
		}
	}
});