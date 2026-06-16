import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react()],

  build: {
    // Output to app/dist/ so serve.cjs can find it
    outDir: "../dist",
    emptyOutDir: true,
  },

  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      "/txt2img": { target: "http://127.0.0.1:8080", changeOrigin: true },
      "/img2img":  { target: "http://127.0.0.1:8080", changeOrigin: true },
      "/v1":       { target: "http://127.0.0.1:8080", changeOrigin: true },
      "/api":      { target: "http://127.0.0.1:1422", changeOrigin: true },
    }
  },
}));
