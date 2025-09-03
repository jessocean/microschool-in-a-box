import type { APIRoute } from 'astro'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: import.meta.env.ANTHROPIC_API_KEY
})

export const POST: APIRoute = async ({ request }) => {
  try {
    const { message } = await request.json()

    // Get recommendations from the network model
    const networkResponse = await fetch('http://localhost:8000/recommendations')
    const { recommendations } = await networkResponse.json()

    // Format recommendations for Claude
    const recommendationsText = recommendations
      .map((rec: any) => `- ${rec.factor}: ${rec.direction} (impact: ${rec.potential.toFixed(2)})`)
      .join('\n')

    // Create the prompt for Claude
    const prompt = `You are a weight management coach. Use the following recommendations from our network model to inform your response, but maintain a natural, conversational tone:

${recommendationsText}

User message: ${message}

Respond in a helpful, empathetic way while incorporating relevant recommendations when appropriate.`

    // Get response from Claude
    const completion = await anthropic.messages.create({
      model: 'claude-3-sonnet-20240229',
      max_tokens: 1000,
      messages: [{ role: 'user', content: prompt }]
    })

    // Extract structured data from Claude's response
    const dataResponse = await anthropic.messages.create({
      model: 'claude-3-sonnet-20240229',
      max_tokens: 1000,
      messages: [{
        role: 'user',
        content: `Extract any mentioned factors and their values from this conversation. Format as JSON:
${completion.content[0].text}`
      }]
    })

    // Update network model with extracted data
    try {
      const extractedData = JSON.parse(dataResponse.content[0].text)
      for (const [factor, value] of Object.entries(extractedData)) {
        await fetch('http://localhost:8000/update_factor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ factor, value: parseFloat(value as string) })
        })
      }
    } catch (error) {
      console.error('Error updating network model:', error)
    }

    return new Response(JSON.stringify({
      response: completion.content[0].text
    }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  } catch (error) {
    console.error('Error processing chat:', error)
    return new Response(JSON.stringify({
      error: 'Failed to process chat message'
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }
} 