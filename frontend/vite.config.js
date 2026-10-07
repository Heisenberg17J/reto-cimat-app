import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El FastAPI sirve el compilado desde /, asi que las rutas deben ser relativas (base: "./").
// En desarrollo, "npm run dev" levanta Vite y manda /api al backend local (arrancalo antes con
// `reto-cimat-servidor --puerto 8000 --sin-navegador`).
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
