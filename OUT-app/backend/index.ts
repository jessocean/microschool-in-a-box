import { serve } from '@hono/node-server';
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import Database from 'sqlite3';
import { initializeDatabase } from './database/migrations.js';
import { DatabaseQueries } from './database/queries.js';

// Import route handlers
import authRoutes from './routes/auth.js';
import userRoutes from './routes/users.js';
import activityRoutes from './routes/activities.js';
import discoveryRoutes from './routes/discovery.js';
import staticRoutes from './routes/static.js';

// Global database instance
export let db: Database.Database;
export let dbQueries: DatabaseQueries;

const app = new Hono();

// Initialize SQLite database
async function initializeApp() {
  try {
    // Create database connection
    db = new Database.Database('./database.sqlite', (err) => {
      if (err) {
        console.error('Error opening database:', err);
        process.exit(1);
      }
      console.log('Connected to SQLite database');
    });

    // Run migrations
    await initializeDatabase(db);
    
    // Initialize query helper
    dbQueries = new DatabaseQueries(db);
    
    console.log('Database initialization completed');
  } catch (error) {
    console.error('Failed to initialize database:', error);
    process.exit(1);
  }
}

// Middleware
app.use('*', logger());
app.use('*', cors({
  origin: ['http://localhost:5173', 'http://localhost:3000'], // Vite dev server and production
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-User-ID'],
  credentials: true
}));

// Add database to context
app.use('*', async (c, next) => {
  c.set('db', db);
  c.set('dbQueries', dbQueries);
  await next();
});

// API Routes
app.route('/api/auth', authRoutes);
app.route('/api/users', userRoutes);
app.route('/api/activities', activityRoutes);
app.route('/api/discovery', discoveryRoutes);

// Serve static files and frontend
app.route('/', staticRoutes);

// API Health check
app.get('/api/health', (c) => {
  return c.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'OUT App API',
    database: db ? 'connected' : 'disconnected'
  });
});

// 404 handler for API routes
app.notFound((c) => {
  const path = c.req.path;
  if (path.startsWith('/api/')) {
    return c.json({
      success: false,
      error: 'API endpoint not found',
      path
    }, 404);
  }
  
  // For non-API routes, let static handler deal with it
  return c.text('Page not found', 404);
});

// Global error handler
app.onError((err, c) => {
  console.error('Unhandled error:', err);
  return c.json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  }, 500);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down gracefully');
  if (db) {
    db.close((err) => {
      if (err) {
        console.error('Error closing database:', err);
      } else {
        console.log('Database connection closed');
      }
      process.exit(0);
    });
  } else {
    process.exit(0);
  }
});

// Start server
const startServer = async () => {
  await initializeApp();
  
  const port = parseInt(process.env.PORT || '3000');
  
  console.log(`Starting OUT App server on port ${port}`);
  
  serve({
    fetch: app.fetch,
    port
  }, (info) => {
    console.log(`Server is running on http://localhost:${info.port}`);
  });
};

// Run the server
startServer().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

export default app;