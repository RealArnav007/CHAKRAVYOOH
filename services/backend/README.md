# Pukar — Command Backend Service

**Project Beacon v4.0** | FastAPI + PostgreSQL (Neon) + PyNaCl | `services/backend/`

Offline-first emergency mesh SOS communication backend. Serves as the cryptographic trust boundary between untrusted P2P mesh relay networks and the web command center.

---

## Quick Start (Development)

```bash
cd services/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Fill in your credentials
uvicorn src.main:app --reload --port 8000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|:---|:---|
| `DATABASE_URL` | Neon PostgreSQL asyncpg connection string |
| `JWT_SECRET_KEY` | 64-char hex string for JWT signing |
| `BACKEND_X25519_PRIVATE_KEY` | 64-char hex Ed25519/X25519 private key for decryption |
| `SMTP_HOST / SMTP_USER / SMTP_PASSWORD` | Brevo SMTP credentials for OTP emails |
| `GROQ_API_KEY` | Groq API key (handled by Rishabh's ML seam) |

In development, if `JWT_SECRET_KEY` and `BACKEND_X25519_PRIVATE_KEY` are empty, **ephemeral keys are auto-generated** and logged at startup.

---

## API Endpoints

| Method | Path | Description |
|:---|:---|:---|
| `POST` | `/api/v1/auth/otp/request` | Request a 6-digit login OTP |
| `POST` | `/api/v1/auth/otp/verify` | Verify OTP and receive JWT |
| `POST` | `/api/v1/sos/ingest` | Ingest a signed SOS packet (Gateway → Backend) |
| `GET` | `/api/v1/sos/{id}/status` | Check SOS delivery status |
| `POST` | `/api/v1/keys/register` | Register a device's Ed25519 + X25519 public keys |
| `GET` | `/api/v1/keys/backend-pubkey` | Get backend's X25519 public key |
| `GET` | `/api/v1/incidents/` | List active incidents (Auth required) |
| `POST` | `/api/v1/incidents/{id}/dispatch` | Dispatch unit to incident (COMMANDER/RESPONDER) |
| `WS` | `/api/v1/ws/dashboard?token=<jwt>` | Realtime dashboard WebSocket |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe |

---

## 10-Step SOS Ingestion Pipeline

```
POST /sos/ingest
  │
  ├─ 1. Schema Validation (Pydantic bounds on lat/lon/scores)
  ├─ 2. Ed25519 Canonical Signature Verification (PyNaCl)
  ├─ 3. Replay Attack Window Check (±5 min timestamp)
  ├─ 4. Idempotent msg_id Deduplication
  ├─ 5. X25519 SealedBox Payload Decryption (PyNaCl)
  ├─ 6. ML Priority Scoring Seam (Groq / deterministic fallback)
  ├─ 7. PostgreSQL SOSReport Persistence
  ├─ 8. Geo-Spatial Incident Correlation (Haversine, 500m/2h)
  ├─ 9. Zone Severity Recalculation (NORMAL→EXTREME state machine)
  └─ 10. WebSocket Realtime Broadcast to Command Dashboard
```

---

## Architecture

```
services/backend/
├── src/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (pydantic-settings)
│   ├── api/v1/              # REST + WebSocket routers
│   ├── auth/                # JWT, OTP, RBAC
│   ├── security/            # Crypto pipeline (Ed25519, X25519, replay)
│   ├── sos/                 # Ingestion pipeline + validation + dedup
│   ├── incidents/           # Correlation engine + lifecycle
│   ├── zones/               # Clustering + severity state machine
│   ├── dispatch/            # Unit dispatch service
│   ├── realtime/            # WebSocket connection manager
│   ├── audit/               # Immutable audit event logger
│   ├── observability/       # Metrics + structured JSON logging
│   └── database/            # SQLAlchemy models + session
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Deployment (Render)

1. Set all environment variables in Render Dashboard.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Health check path: `/health`
