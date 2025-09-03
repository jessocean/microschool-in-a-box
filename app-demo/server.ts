import { serve } from "https://deno.land/std/http/server.ts"
import { Server } from "https://deno.land/x/socket_io@0.2.0/mod.ts"

const io = new Server()

type ChatMessage = {
  username: string
  message: string
  timestamp: number
}

const messages: ChatMessage[] = []

io.on("connection", (socket) => {
  console.log(`Client connected: ${socket.id}`)

  socket.emit("previous-messages", messages)

  socket.on("chat-message", (data: ChatMessage) => {
    messages.push(data)
    io.emit("new-message", data)
  })

  socket.on("disconnect", () => {
    console.log(`Client disconnected: ${socket.id}`)
  })
})

const handler = async (req: Request): Promise<Response> => {
  const upgrade = req.headers.get("upgrade") || ""
  if (upgrade.toLowerCase() === "websocket") {
    return io.handler()(req)
  }

  const filepath = new URL(".", import.meta.url).pathname + "public/index.html"
  const file = await Deno.readFile(filepath)
  return new Response(file, {
    headers: { "content-type": "text/html" },
  })
}

console.log("Chat server running on http://localhost:3000")
await serve(handler, { port: 3000 }) 