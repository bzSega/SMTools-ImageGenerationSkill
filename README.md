# SMTools Image Generation Skill

OpenClaw skill for generating images from text prompts using AI models.

## Providers

| Provider | Type | Models | Env Variable |
|----------|------|--------|-------------|
| **OpenRouter** (default) | Synchronous | `openai/gpt-image-1`, `google/imagen-4`, `stabilityai/stable-diffusion-3` | `OPENROUTER_API_KEY` |
| **Kie.ai** | Async (task-based) | `flux-ai`, `midjourney`, `google-4o-image`, `ghibli-ai` | `KIE_API_KEY` |

## Installation

```bash
# Clone
git clone https://github.com/bzSega/SMTools-ImageGenerationSkill.git

# Copy to OpenClaw skills directory
cp -r SMTools-ImageGenerationSkill ~/.openclaw/skills/smtools-image-generation

# Setup
cd ~/.openclaw/skills/smtools-image-generation
bash setup.sh
```

Edit `.env` and add your API key(s):
```bash
OPENROUTER_API_KEY=your_key_here
# KIE_API_KEY=your_key_here  # optional
```

## Usage

The skill activates automatically in OpenClaw when you ask to generate an image.

### Manual CLI usage

```bash
# Generate with default provider (OpenRouter)
python3 scripts/generate.py -p "A cat in space"

# Use a specific model
python3 scripts/generate.py -p "Cyberpunk cityscape" -m "google/imagen-4"

# Use Kie.ai provider
python3 scripts/generate.py -p "Studio Ghibli forest" --provider kie -m ghibli-ai

# Custom output path
python3 scripts/generate.py -p "A red fox" -o /tmp/fox.png

# List available models
python3 scripts/generate.py --provider openrouter --list-models
```

### Output

JSON to stdout:
```json
{
  "status": "ok",
  "image_path": "/absolute/path/to/output/img_20260314_153000.png",
  "model": "openai/gpt-image-1",
  "provider": "openrouter"
}
```

## Configuration

`config.json` (created by `setup.sh` from `assets/config.example.json`):

```json
{
  "default_provider": "openrouter",
  "output_dir": "output",
  "providers": {
    "openrouter": {
      "default_model": "openai/gpt-image-1",
      "max_tokens": 4096
    },
    "kie": {
      "default_model": "google-4o-image",
      "poll_interval": 5,
      "max_wait": 300
    }
  }
}
```

Environment variables override config values:
- `IMAGE_DEFAULT_PROVIDER` — override default provider
- `IMAGE_OUTPUT_DIR` — override output directory

## Diagnostics

```bash
bash check.sh
```

## Project Structure

```
├── SKILL.md                    # OpenClaw skill definition
├── README.md
├── setup.sh                    # First-time setup
├── check.sh                    # Diagnostics
├── requirements.txt
├── assets/
│   └── config.example.json
├── scripts/
│   ├── generate.py             # CLI entry point
│   ├── config_manager.py       # Config loading
│   └── providers/
│       ├── __init__.py
│       ├── base_provider.py    # Abstract base class
│       ├── openrouter_provider.py
│       └── kie_provider.py     # Stub with TODOs
└── output/                     # Generated images (gitignored)
```

## Adding a New Provider

1. Create `scripts/providers/your_provider.py` implementing `BaseImageProvider`
2. Register it in `scripts/providers/__init__.py` `PROVIDERS` dict
3. Add config section in `assets/config.example.json`
4. Add env var mapping in `scripts/config_manager.py` `get_api_key()`
