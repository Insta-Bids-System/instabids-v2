# Environment Files Comparison Report
*Generated: August 12, 2025*

## File Comparison Results

### 1. Root `.env` vs `ai-agents/.env`
**Status: IDENTICAL** ✅
- Both files are 76 lines
- Byte-for-byte identical
- No differences found

### 2. Root `.env` vs `.env.docker`
**Status: DIFFERENT** ⚠️

#### Variables in `.env.docker` NOT in root `.env`:
```bash
# Database (Docker-specific)
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password

# MailHog (Docker-specific)
SMTP_HOST=localhost
SMTP_PORT=1025
```

#### Variables in root `.env` NOT in `.env.docker`:
- All AI API keys (ANTHROPIC_API_KEY, XAI_API_KEY, LEONARDO_API_KEY, etc.)
- VITE_* frontend variables
- Google Maps API key
- Feature flags
- CORS settings
- Environment settings (NODE_ENV, PYTHON_ENV, LOG_LEVEL)

### 3. Root `.env` vs `web/.env.local`
**Status: MINIMAL OVERLAP** ⚠️

`web/.env.local` contains ONLY:
```bash
VITE_API_URL=http://localhost:8008
```

This is ALREADY in root `.env`, so `web/.env.local` is redundant.

## Variables Unique to Each File

### Unique to `.env.docker`:
1. `POSTGRES_DB=postgres`
2. `POSTGRES_USER=postgres`
3. `POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password`
4. `SMTP_HOST=localhost`
5. `SMTP_PORT=1025`

### Unique to root `.env`:
- All other 70+ variables

### Unique to `web/.env.local`:
- NONE (its single variable is already in root)

## Recommendation

Add these 5 variables from `.env.docker` to root `.env`:
```bash
# ====================
# DOCKER/DATABASE
# ====================
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password

# ====================
# EMAIL (MailHog)
# ====================
SMTP_HOST=localhost
SMTP_PORT=1025
```

Then all files can be safely deleted except root `.env`!