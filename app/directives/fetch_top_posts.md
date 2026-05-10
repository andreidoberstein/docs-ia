# Top 5 Reddit Posts por Engajamento

## Goal
Buscar os 100 posts mais recentes de dois subreddits (`r/n8n` e `r/automation`) e extrair os 5 posts com maior engajamento e relevância da semana corrente de cada tópico. O resultado é salvo em `.tmp/` como JSON para uso posterior.

## Inputs
- `subreddits`: Lista de subreddits alvo (fixo: `['n8n', 'automation']`)
- `fetch_limit`: Número de posts a buscar por subreddit (padrão: 100)
- `time_window_days`: Janela de tempo em dias para filtrar posts (padrão: 7 dias)
- `top_n`: Número de posts a retornar por subreddit (padrão: 5)

## Tools to use
- `execution/fetch_reddit_posts.py`: Busca os posts via Reddit Public JSON API (sem autenticação), filtra por janela de tempo, calcula score de engajamento e retorna os top N.

## Engagement Score Formula
```
engagement_score = (score * upvote_ratio) + (num_comments * 2)
```
- `score`: Número de upvotes líquidos
- `upvote_ratio`: Proporção de votos positivos (0 a 1)
- `num_comments`: Número de comentários (peso 2x, pois indica discussão ativa)

## Output
- `.tmp/top_posts_{subreddit}.json` para cada subreddit, contendo:
  - `title`: Título do post
  - `author`: Autor
  - `url`: Link direto para o post no Reddit
  - `score`: Upvotes líquidos
  - `upvote_ratio`: Proporção de votos positivos
  - `num_comments`: Número de comentários
  - `engagement_score`: Score calculado
  - `created_utc`: Data/hora de criação (UTC)
  - `flair`: Flair do post (se houver)

## Edge Cases
- Reddit retorna 429 (rate limit): aguardar e tentar novamente com backoff exponencial.
- Subreddit privado ou inexistente: logar erro e pular.
- Posts sem upvote_ratio (valor null): tratar como 0.5.
- Posts mais antigos que a janela de tempo são descartados mesmo se vieram na resposta da API.

## Notes
- Usa a Reddit Public JSON API (`reddit.com/r/{sub}/new.json`), sem necessidade de credenciais.
- User-Agent deve ser definido para evitar bloqueio (ex: `"top5-reddit-bot/1.0"`).
- A API pública tem limite de 100 posts por request (`?limit=100`).
