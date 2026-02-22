import os
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    # Point Claude Agent SDK at LiteLLM Proxy (not Anthropic)
    os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:4000"
    # LiteLLM expects an API key field; can be any string unless you enabled auth on the proxy
    os.environ["ANTHROPIC_API_KEY"] = "sk-local"

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful coding assistant.",
        # model="ollama-llama3.2",  # must match model_name in config.yaml
        model="ollama-qwen3",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        max_turns=10,
    )

    print("test")

    async with ClaudeSDKClient(options=options) as client:
        await client.query("write a python function that prints the first 10 fibonacci numbers")
        async for msg in client.receive_response():
            # Stream text content blocks
            if hasattr(msg, "content") and msg.content:
                for block in msg.content:
                    if hasattr(block, "text") and block.text:
                        print(block.text, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
