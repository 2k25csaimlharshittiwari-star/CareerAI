# CareerAI Production Foundation v3

CareerAI is an AI-powered student career intelligence platform. This upgrade keeps the working FastAPI prototype and adds production-oriented security, configuration, CRUD deletion, resume parsing, internship matching, account deletion, health checks, Docker support, persistent data volumes, and a clearer separation between AI estimates and verified opportunities.

## Run locally
```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```
Open `http://127.0.0.1:8000`.

## Production
1. Copy `.env.example` to `.env`.
2. Set a random `CAREERAI_SECRET` (32+ characters).
3. Set `CAREERAI_ALLOWED_ORIGINS` to your real HTTPS domain.
4. Run `docker compose up -d --build`.
5. Put the service behind a managed HTTPS reverse proxy/load balancer.
6. Back up the persistent `careerai_data` volume.

FastAPI's production guidance recommends HTTPS, startup/restart handling and resource planning; a TLS termination proxy can handle certificates while forwarding traffic to the FastAPI app. See the official FastAPI deployment documentation.

## Important
- The current opportunity cards are **AI/demo estimates**, not verified live job or hackathon openings.
- The resume analyzer parses PDF/DOCX/TXT and produces a heuristic score. It is not a recruiter or ATS guarantee.
- SQLite is retained for this MVP foundation. For high traffic, migrate the persistence layer to PostgreSQL and add managed object storage for resumes.
- Never commit `.env`, secrets, real student data, or the `data/` directory to source control.

## Optional real LLM integration

CareerAI can use the OpenAI Responses API for personalized career analysis, recommendations, and the AI Mentor. If `OPENAI_API_KEY` is not configured, the app safely falls back to its local heuristic engine. Keep the API key on the server in environment variables; never put it in frontend JavaScript or commit it to Git.

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` (default `gpt-5.6-luna`), then restart the server. API usage can incur charges according to the selected model and your API account.
