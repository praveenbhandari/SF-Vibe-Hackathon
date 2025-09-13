/**
 * AI service routes for generating notes and answering questions
 */
import { Router, type Request, type Response } from 'express'
import Groq from 'groq-sdk'

const router = Router()

// Initialize Groq client
const getGroqClient = () => {
  const apiKey = process.env.GROQ_API_KEY
  if (!apiKey) {
    throw new Error('GROQ_API_KEY environment variable is required')
  }
  return new Groq({ apiKey })
}

/**
 * Generate AI notes from extracted text
 * POST /api/ai/generate-notes
 */
router.post('/generate-notes', async (req: Request, res: Response): Promise<void> => {
  try {
    const { text, filename, courseTitle } = req.body

    if (!text) {
      res.status(400).json({
        success: false,
        error: 'Text content is required'
      })
      return
    }

    const groq = getGroqClient()
    const model = process.env.GROQ_MODEL || 'llama3-8b-8192'

    // Create a comprehensive prompt for note generation
    const prompt = `You are an expert academic note-taker. Generate comprehensive, well-structured notes from the following content.

${courseTitle ? `Course: ${courseTitle}` : ''}
${filename ? `Source: ${filename}` : ''}

Content:
${text}

Please create detailed notes that include:
1. Key concepts and definitions
2. Important points and main ideas
3. Examples and explanations
4. Summary of key takeaways

Format the notes in a clear, organized manner with appropriate headings and bullet points.`

    const completion = await groq.chat.completions.create({
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      model: model,
      temperature: 0.3,
      max_tokens: 2048,
      top_p: 1,
      stream: false
    })

    const generatedNotes = completion.choices[0]?.message?.content

    if (!generatedNotes) {
      res.status(500).json({
        success: false,
        error: 'Failed to generate notes'
      })
      return
    }

    res.json({
      success: true,
      notes: generatedNotes,
      metadata: {
        filename,
        courseTitle,
        generatedAt: new Date().toISOString(),
        model: model
      }
    })
  } catch (error) {
    console.error('Generate notes error:', error)
    
    if (error instanceof Error && error.message.includes('GROQ_API_KEY')) {
      res.status(500).json({
        success: false,
        error: 'GROQ API key not configured'
      })
    } else {
      res.status(500).json({
        success: false,
        error: 'Failed to generate notes'
      })
    }
  }
})

/**
 * Answer questions based on context
 * POST /api/ai/answer-question
 */
router.post('/answer-question', async (req: Request, res: Response): Promise<void> => {
  try {
    const { question, context, courseTitle } = req.body

    if (!question) {
      res.status(400).json({
        success: false,
        error: 'Question is required'
      })
      return
    }

    const groq = getGroqClient()
    const model = process.env.GROQ_MODEL || 'llama3-8b-8192'

    // Create a prompt for question answering
    let prompt = `You are an expert academic assistant. Answer the following question based on the provided context.

${courseTitle ? `Course: ${courseTitle}` : ''}

Question: ${question}

`

    if (context) {
      prompt += `Context:
${context}

`
    }

    prompt += `Please provide a comprehensive, accurate answer. If the context doesn't contain enough information to fully answer the question, indicate what additional information might be needed.`

    const completion = await groq.chat.completions.create({
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      model: model,
      temperature: 0.2,
      max_tokens: 1024,
      top_p: 1,
      stream: false
    })

    const answer = completion.choices[0]?.message?.content

    if (!answer) {
      res.status(500).json({
        success: false,
        error: 'Failed to generate answer'
      })
      return
    }

    res.json({
      success: true,
      answer: answer,
      metadata: {
        question,
        courseTitle,
        answeredAt: new Date().toISOString(),
        model: model,
        hasContext: !!context
      }
    })
  } catch (error) {
    console.error('Answer question error:', error)
    
    if (error instanceof Error && error.message.includes('GROQ_API_KEY')) {
      res.status(500).json({
        success: false,
        error: 'GROQ API key not configured'
      })
    } else {
      res.status(500).json({
        success: false,
        error: 'Failed to generate answer'
      })
    }
  }
})

/**
 * Get AI service status
 * GET /api/ai/status
 */
router.get('/status', async (req: Request, res: Response): Promise<void> => {
  try {
    const hasGroqKey = !!process.env.GROQ_API_KEY
    const model = process.env.GROQ_MODEL || 'llama3-8b-8192'

    res.json({
      success: true,
      status: {
        groqConfigured: hasGroqKey,
        model: model,
        available: hasGroqKey
      }
    })
  } catch (error) {
    console.error('AI status error:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to get AI service status'
    })
  }
})

export default router