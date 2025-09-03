import { defineSchema, defineTable } from 'astro:db'

const schema = defineSchema({
  users: defineTable({
    id: 'string',
    networkState: {
      type: 'json',
      schema: {
        factors: 'record',
        relationships: 'array'
      }
    },
    conversationHistory: {
      type: 'array',
      schema: {
        timestamp: 'date',
        message: 'string',
        response: 'string'
      }
    }
  })
})

export default schema 