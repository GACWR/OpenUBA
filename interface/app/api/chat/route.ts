export async function POST(req: Request) {
    try {
        const body = await req.json()
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        const response = await fetch(`${apiUrl}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })

        if (!response.ok) {
            const error = await response.text()
            return new Response(error, { status: response.status })
        }

        // stream SSE through directly to the client
        return new Response(response.body, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
        })
    } catch (error) {
        console.error('Chat API error:', error)
        return new Response(
            JSON.stringify({ detail: 'Internal server error' }),
            { status: 500, headers: { 'Content-Type': 'application/json' } }
        )
    }
}
