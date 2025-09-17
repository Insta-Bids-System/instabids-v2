import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from root directory
  const env = loadEnv(mode, path.resolve(__dirname, '..'), '')
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      open: true,
      host: '0.0.0.0',
      // Fix HMR/WebSocket for Docker environment
      hmr: {
        clientPort: 5173,
        host: 'localhost',
        protocol: 'ws',
        port: 5173
      },
      proxy: {
        '/api': {
          // Smart proxy target detection: localhost for local dev, container name for Docker
          target: process.env.DOCKER_ENV === 'true' ? 'http://instabids-backend:8008' : 'http://localhost:8008',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            const backendTarget = process.env.DOCKER_ENV === 'true' ? 'instabids-backend:8008' : 'localhost:8008';
            
            // Add error handling with fallback
            proxy.on('error', (err, req, res) => {
              console.log(`Proxy error connecting to ${backendTarget}:`, err.message);
              // Try fallback if initial target fails
              if (res.writeHead && !res.headersSent) {
                res.writeHead(502, {
                  'Content-Type': 'application/json',
                });
                res.end(JSON.stringify({ 
                  error: `Failed to connect to backend at ${backendTarget}`,
                  suggestion: 'Check if backend is running'
                }));
              }
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log(`Proxying: ${req.method} ${req.url} → ${backendTarget}`);
            });
          },
        },
        '/ws': {
          target: process.env.DOCKER_ENV === 'true' ? 'ws://instabids-backend:8008' : 'ws://localhost:8008',
          ws: true,
          changeOrigin: true,
          configure: (proxy, options) => {
            proxy.on('error', (err) => {
              const wsTarget = process.env.DOCKER_ENV === 'true' ? 'instabids-backend:8008' : 'localhost:8008';
              console.log(`WebSocket proxy error connecting to ${wsTarget}:`, err.message);
            });
          },
        },
      },
    },
    envDir: '..',
  }
})