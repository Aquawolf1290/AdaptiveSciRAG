import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const target = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/papers": { target, changeOrigin: true },
      "/chat": { target, changeOrigin: true },
      "/figures": { target, changeOrigin: true },
      "/health": { target, changeOrigin: true },
    },
  },
});
