import os
import asyncio
import json
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    # Point Claude Agent SDK at LiteLLM Proxy (not Anthropic)
    os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:4000"
    # LiteLLM expects an API key field; can be any string unless you enabled auth on the proxy
    os.environ["ANTHROPIC_API_KEY"] = "sk-local"

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful coding assistant.",
        # model="ollama-llama3.2",  # must match model_name in config.yaml
        # model="ollama-qwen3",
        model='gemini-2.5-flash',
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="acceptEdits",
        max_turns=10,
        thinking={"type": "adaptive"},
    )

    # query = "read loop.py in this directory and count the number of lines of code. Then write that number to a file called loc.txt."
    query = "how is the weather in sf?"

    max_retries = 5
    base_delay = 10  # seconds

    async with ClaudeSDKClient(options=options) as client:
        # Send query with retry on rate limit
        for attempt in range(1, max_retries + 1):
            try:
                await client.query(query)
                break
            except Exception as e:
                if "rate" in str(e).lower() or "429" in str(e):
                    delay = base_delay * attempt
                    print(f"Rate limited on query (attempt {attempt}/{max_retries}), retrying in {delay}s: {e}", flush=True)
                    await asyncio.sleep(delay)
                else:
                    raise

        # Receive response with retry on rate limit
        retry_count = 0
        while True:
            try:
                async for msg in client.receive_response():
                    await asyncio.sleep(3)
                    retry_count = 0  # reset on successful message

                    msg_type = type(msg).__name__
                    print(f"\n--- {msg_type} ---", flush=True)

                    # Print all non-content fields of the message
                    for key, val in vars(msg).items():
                        if key != "content":
                            print(f"  {key}: {val}", flush=True)

                    if hasattr(msg, "content") and msg.content:
                        for block in msg.content:
                            block_type = getattr(block, "type", type(block).__name__)

                            if block_type == "thinking" and getattr(block, "thinking", None):
                                print(f"\n[Thinking]\n{block.thinking}\n", flush=True)

                            elif block_type == "tool_use":
                                print(f"\n[Tool Call: {block.name}]", flush=True)
                                if getattr(block, "input", None):
                                    print(json.dumps(block.input, indent=2), flush=True)

                            elif block_type == "tool_result":
                                content = getattr(block, "content", None)
                                if content:
                                    text = content if isinstance(content, str) else str(content)
                                    print(f"\n[Tool Result]\n{text}\n", flush=True)

                            elif getattr(block, "text", None):
                                print(block.text, end="", flush=True)
                    else:
                        # Fallback: dump full message if no content attribute
                        try:
                            print(f"  (raw) {vars(msg)}", flush=True)
                        except TypeError:
                            print(f"  (raw) {msg}", flush=True)

                break  # done, exit retry loop

            except Exception as e:
                if "rate" in str(e).lower() or "429" in str(e):
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    delay = base_delay * retry_count
                    print(f"Rate limited on response (attempt {retry_count}/{max_retries}), retrying in {delay}s: {e}", flush=True)
                    await asyncio.sleep(delay)
                else:
                    raise

if __name__ == "__main__":
    asyncio.run(main())
