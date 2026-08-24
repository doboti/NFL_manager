import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    watch: {
      // Docker Desktop on Windows bind-mounts don't reliably deliver native
      // filesystem change events to the container, so HMR silently serves
      // stale transforms until the dev server is restarted. Polling costs a
      // bit of CPU but always picks up host-side edits.
      usePolling: true,
      interval: 300,
    },
  },
});
