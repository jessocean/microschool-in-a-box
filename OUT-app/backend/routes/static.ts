import { Hono } from "hono";
import { serveStatic } from "hono/serve-static";

const staticRoutes = new Hono();

// Serve frontend files
staticRoutes.use("/*", serveStatic({
  root: "./frontend",
  index: "index.html"
}));

// Health check endpoint
staticRoutes.get("/health", (c) => {
  return c.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    service: "OUT App API"
  });
});

export default staticRoutes;