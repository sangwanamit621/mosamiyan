---
trigger: always_on
description: Prohibits hardcoding any credentials, API keys, secrets, or tokens in code files.
---

# No Hardcoded Credentials Rule

- **Strict Prohibition**: Never hardcode API keys, secrets, passwords, or authentication tokens directly in any source code, template, static file, script, or configuration file.
- **Environment Driven**: Always retrieve credentials from environment variables (`.env`, `os.environ`, or config classes).
- **Client Assets**: Public/client-side keys must be passed dynamically at runtime from backend configuration, never hardcoded in static JS/HTML assets.
- **Sample Files**: `.env.example` must contain empty placeholders only.
