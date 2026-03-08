from agents import Agent
from agents.mcp import MCPServerHTTP

reo_mcp = MCPServerHTTP(
    url="http://10.10.0.71:8001/mcp"
)

agent = Agent(
    name="Reo Assistant",
    instructions="Help users explore reo.dev segments, developers, accounts and audiences.",
    mcp_servers=[reo_mcp],
)

while True:
    q = input(">> ")
    print(agent.run(q))
