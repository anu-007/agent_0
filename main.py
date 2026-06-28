import argparse
import asyncio

class AgentServer:
    def __init__(self, host: str ="localhost", port: int = 3000, provider: str = "anthropic-haiku"):
        self.host = host
        self.port = port
        self.provider = provider

    def handle_task(self):
        pass

    async def start(self):
        server = await asyncio.start_server(self.handle_task, self.host, self.port)

        async with server:
            print("agent 0 is running")
            await server.serve_forever()
    

def main():
    parser = argparse.ArgumentParser(description="Agent 0, a intern coding agent")
    parser.add_argument('--provider', type=str, default="anthropic-haiku", help="llm model")
    parser.add_argument('--port', type=int, default=3000, help='Port to run the server on (default: 3000)')

    args = parser.parse_args()
    agent_server = AgentServer(host="localhost", port=args.port)
    try:
        asyncio.run(agent_server.start())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
