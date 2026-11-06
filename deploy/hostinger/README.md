# CoVakeel on the Hostinger default domain

The `covakeel@gmail.com` account has the KVM 4 VPS at `201.18.201.90`.
Its default domain is `srv2082168.hstgr.cloud`. This deployment runs the
website and app, FastAPI/Gemini, MongoDB, and the Chroma index on that VPS.
Only Caddy publishes ports 80 and 443. Nginx serves both frontend pages and
forwards `/api/` to FastAPI. MongoDB and FastAPI are private Docker services.

The former `/opt/covakeel` stack used the same domain. Its PostgreSQL data,
files, and Docker volumes should be kept as a rollback backup. Stop it with
`docker compose ... down` **without `-v`** only after testing the new stack.

## Transfer and stage

Copy this checkout, including its uncommitted frontend changes, plus the
ignored Chroma index and embedding cache into `/opt/covakeel-rag`. Exclude
local `.env` files, `.git`, node_modules, and the local MongoDB data folder.
`backend/chroma_db/local_manifest.json` should list the RTI and two GST Acts.

Create `/opt/covakeel-rag/.env` from `.env.example` with strong random MongoDB
and JWT secrets and the Gemini key. Keep it mode 600. Set `APP_DOMAIN` to
`srv2082168.hstgr.cloud` and `TLS_EMAIL` to `covakeel@gmail.com`.

```bash
cd /opt/covakeel-rag
docker compose --env-file .env -f compose.hostinger.yml config --quiet
docker compose --env-file .env -f compose.hostinger.yml build backend frontend
docker compose --env-file .env -f compose.hostinger.yml up -d mongodb backend frontend
```

The frontend can be checked inside Docker before switching traffic:

```bash
docker compose --env-file .env -f compose.hostinger.yml exec -T frontend \
  wget -qO- http://localhost/api/
```

For existing local users and chats, export with
`backend/tools/migrate_mongodb.py export FILE`, transfer the private file over
SSH, and import it into the empty VPS MongoDB with the same script. The export
contains private data; remove transfer copies after verifying the import.

## Switch the default domain

Back up the old PostgreSQL database and `/opt/covakeel/deploy` configuration.
Then stop the old stack **without deleting its volumes**:

```bash
docker compose --env-file /opt/covakeel/deploy/.env.production \
  -f /opt/covakeel/deploy/docker-compose.yml down
cd /opt/covakeel-rag
docker compose --env-file .env -f compose.hostinger.yml up -d caddy
```

The new Caddy uses the existing `deploy_caddy_data` certificate volume, so
the default domain keeps its TLS certificate. Verify the HTTPS homepage,
`/app/`, `/api/`, account login/signup, and a sourced GST answer. The old
stack can be restarted from its original Compose file if rollback is needed.
