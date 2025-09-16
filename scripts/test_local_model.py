from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(
        id="models/gpt-oss-120b-F16.gguf",
        base_url="http://localhost:8080/v1",   # your llama.cpp server
        api_key="helloworld"                      # anything non-empty is fine
    ),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    tool_choice="auto",
)

agent.print_response("Find the ROMA repo on GitHub and give me the URL.")