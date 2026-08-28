# Antigravity Agent Guidelines

## 🔒 Security & Credential Management Policy

1. **Zero Hardcoded Credentials**:
   - **NEVER** hardcode any API key, access token, secret, password, private key, or sensitive credential in any source code file, template, static asset (`.js`, `.html`, `.css`), configuration file, script, or documentation.
   - Any sensitive parameter or API key must be retrieved exclusively from environment variables (e.g., `.env`, `os.environ`, Pydantic `BaseSettings`, or runtime configuration injection).

2. **Environment & Sample Files**:
   - Real secret values belong strictly in `.env` (which must be gitignored).
   - `.env.example` must contain only key names with empty values or non-sensitive dummy placeholders (e.g. `API_KEY=`).

3. **Frontend / Client-side Security**:
   - Never embed secret keys in client-side bundles or static scripts.
   - If a public key (or map tile key) is required by client code, pass it dynamically at runtime through backend template rendering (e.g., Jinja2 context) or an authenticated backend endpoint, never committed as raw strings in JavaScript files.

4. **Continuous Verification**:
   - Audit all code modifications and diffs before saving to verify that no credentials or secrets have been accidentally introduced.
