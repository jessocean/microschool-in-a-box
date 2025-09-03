import { useState, useEffect } from 'react'

interface Message {
  timestamp: Date
  message: string
  response: string
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    setIsLoading(true)
    const userMessage = input.trim()
    setInput('')

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMessage })
      })

      const data = await response.json()
      
      setMessages(prev => [...prev, {
        timestamp: new Date(),
        message: userMessage,
        response: data.response
      }])
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className="message-group">
            <div className="user-message">{msg.message}</div>
            <div className="assistant-message">{msg.response}</div>
          </div>
        ))}
        {isLoading && <div className="loading">Thinking...</div>}
      </div>
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          Send
        </button>
      </form>
      <style>{`
        .chat-container {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          height: 100vh;
          display: flex;
          flex-direction: column;
        }
        .messages {
          flex-grow: 1;
          overflow-y: auto;
          margin-bottom: 20px;
        }
        .message-group {
          margin-bottom: 20px;
        }
        .user-message {
          background: #f0f0f0;
          padding: 10px;
          border-radius: 10px;
          margin-bottom: 10px;
        }
        .assistant-message {
          background: #e3f2fd;
          padding: 10px;
          border-radius: 10px;
        }
        .input-form {
          display: flex;
          gap: 10px;
        }
        input {
          flex-grow: 1;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 5px;
        }
        button {
          padding: 10px 20px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
        }
        button:disabled {
          background: #ccc;
        }
        .loading {
          text-align: center;
          color: #666;
          padding: 10px;
        }
      `}</style>
    </div>
  )
} 