import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import authRoutes from './routes/auth.js'
import canvasRoutes from './routes/canvas.js'
import aiRoutes from './routes/ai.js'
import filesRoutes from './routes/files.js'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001

// Middleware
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:5174', 'http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}))
app.use(express.json({ limit: '50mb' }))
app.use(express.urlencoded({ extended: true, limit: '50mb' }))

// Routes
app.use('/api/auth', authRoutes)
app.use('/api/canvas', canvasRoutes)
app.use('/api/ai', aiRoutes)
app.use('/api/files', filesRoutes)

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    services: {
      canvas: 'available',
      ai: process.env.GROQ_API_KEY ? 'configured' : 'not configured'
    }
  })
})

// API info endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Canvas AI Backend',
    version: '1.0.0',
    endpoints: {
      auth: '/api/auth',
      canvas: '/api/canvas',
      ai: '/api/ai',
      files: '/api/files',
      health: '/health'
    }
  })
})

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Error:', err.stack)
  res.status(500).json({ 
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong!'
  })
})

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ 
    success: false,
    error: 'Route not found',
    path: req.originalUrl
  })
})

export default app
