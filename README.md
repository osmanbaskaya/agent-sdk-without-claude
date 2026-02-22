uv sync
ollama pull qwen3:8b
uv run litellm --config config.yaml &
python loop.py
