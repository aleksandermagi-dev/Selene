import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "node:fs";

const pkg = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf-8"));
const buildLabel = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

export default defineConfig({
  root: "src-ui",
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
    __BUILD_LABEL__: JSON.stringify(buildLabel)
  },
  build: {
    outDir: "../dist-ui",
    emptyOutDir: true
  },
  server: {
    host: "127.0.0.1",
    port: 5173
  }
});
