# GitHub Secrets Configuration for Instabids

## ⚠️ IMPORTANT: Add these secrets to GitHub immediately after pushing!

### Where to add secrets:
1. Go to: https://github.com/Insta-Bids-System/instabids/settings/secrets/actions
2. Click "New repository secret" for each entry below
3. Use the values from your SECRETS_DO_NOT_COMMIT.txt file

### Required Secrets:

| Secret Name | Description |
|------------|-------------|
| `SUPABASE_URL` | Your Supabase project URL (format: https://[PROJECT_ID].supabase.co) |
| `SUPABASE_ANON_KEY` | Your Supabase anonymous key (public key) |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service role key (keep this secret!) |
| `ANTHROPIC_API_KEY` | Your Anthropic Claude API key |
| `XAI_API_KEY` | Your xAI (Grok) API key |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GOOGLE_MAPS_API_KEY` | Your Google Maps API key |
| `VITE_OPENAI_API_KEY` | Same as OPENAI_API_KEY (for frontend) |

### Frontend Environment Variables (for deployment):

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Same as SUPABASE_URL |
| `VITE_SUPABASE_ANON_KEY` | Same as SUPABASE_ANON_KEY |
| `VITE_API_URL` | Update based on deployment URL |
| `VITE_PUBLIC_URL` | Update based on deployment URL |

### Optional (for future features):

- `STRIPE_PUBLIC_KEY` - For payment processing
- `STRIPE_SECRET_KEY` - For payment processing
- `STRIPE_WEBHOOK_SECRET` - For Stripe webhooks
- `GROQ_API_KEY` - Alternative AI provider

## 🔒 Security Notes:

1. These secrets are stored encrypted in GitHub
2. They're only accessible to GitHub Actions and authorized users
3. Never commit actual secret values to your code
4. The `.env` file should remain in `.gitignore`
5. Keep your SECRETS_DO_NOT_COMMIT.txt file safe and local

## 📝 After Adding Secrets:

1. Your GitHub Actions workflows can access these secrets
2. Deployment platforms (Vercel, Netlify, etc.) need these added separately
3. Local development still uses the `.env` file

## 🚨 Important Files:

- `SECRETS_DO_NOT_COMMIT.txt` - Contains actual secret values (DO NOT PUSH!)
- `.env` - Local development secrets (already in .gitignore)
- This file - Documentation only (safe to push)

---

**Action Required**: Add all secrets listed above to GitHub after pushing the code!