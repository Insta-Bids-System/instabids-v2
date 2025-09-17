# LLM Configuration

## Model Assignments
- CIA/CoIA: Claude 3.5 Sonnet (customer-facing)
- JAA: Grok 4 (speed) or O3 (analysis)
- CDA/EAA: Grok 4 (real-time search)
- SMA/CHO: Groq/Kimi K2 (cost optimization)
- CRA: O3-deep-research (complex analysis)

## API Keys Required
- ANTHROPIC_API_KEY
- XAI_API_KEY  
- OPENAI_API_KEY
- GROQ_API_KEY
- GEMINI_API_KEY_1-5 (fallbacks)

## Cost Optimization Strategy
- Customer-facing: Quality first (Claude 3.5)
- Backend processing: Cost optimization (Groq)
- Research tasks: Premium when needed (O3)