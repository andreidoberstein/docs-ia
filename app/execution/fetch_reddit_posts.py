"""
fetch_reddit_posts.py
---------------------
Busca os 100 posts mais recentes de subreddits definidos (r/n8n e r/automation),
filtra os da semana corrente, calcula engagement score e salva os top 5 de cada
subreddit em .tmp/top_posts_{subreddit}.json

Não requer autenticação — usa a Reddit Public JSON API.
"""

import json
import time
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

SUBREDDITS = ["n8n", "automation"]
FETCH_LIMIT = 100           # Reddit permite max 100 por request
TIME_WINDOW_DAYS = 7        # Filtrar posts da última semana
TOP_N = 5                   # Top N posts por subreddit
OUTPUT_DIR = Path(__file__).parent.parent / ".tmp"
HEADERS = {"User-Agent": "top5-reddit-bot/1.0"}

BASE_URL = "https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"

# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------

def calculate_engagement_score(post: dict) -> float:
    """
    Calcula o score de engajamento conforme a diretriz:
        engagement_score = (score * upvote_ratio) + (num_comments * 2)
    """
    score = post.get("score", 0) or 0
    upvote_ratio = post.get("upvote_ratio") or 0.5
    num_comments = post.get("num_comments", 0) or 0
    return (score * upvote_ratio) + (num_comments * 2)


def fetch_posts(subreddit: str, limit: int = FETCH_LIMIT, retries: int = 3) -> list:
    """
    Busca os posts mais recentes de um subreddit via Reddit Public JSON API.
    Implementa backoff exponencial em caso de rate limit (429).
    """
    url = BASE_URL.format(subreddit=subreddit, limit=limit)
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)

            if response.status_code == 429:
                wait = 2 ** attempt * 5  # 5s, 10s, 20s
                print(f"  [WARN] Rate limit atingido em r/{subreddit}. Aguardando {wait}s...")
                time.sleep(wait)
                continue

            if response.status_code == 404:
                print(f"  [ERROR] Subreddit r/{subreddit} não encontrado.")
                return []

            if response.status_code == 403:
                print(f"  [ERROR] Subreddit r/{subreddit} é privado ou restrito.")
                return []

            response.raise_for_status()

            data = response.json()
            posts = [child["data"] for child in data["data"]["children"]]
            print(f"  [OK] Buscados {len(posts)} posts de r/{subreddit}")
            return posts

        except requests.RequestException as e:
            print(f"  [ERROR] Falha ao buscar r/{subreddit} (tentativa {attempt + 1}): {e}")
            time.sleep(2 ** attempt)

    print(f"  [ERROR] Todas as tentativas falharam para r/{subreddit}.")
    return []


def filter_by_time_window(posts: list, days: int = TIME_WINDOW_DAYS) -> list:
    """
    Filtra posts criados dentro da janela de tempo (últimos N dias).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = [
        p for p in posts
        if datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc) >= cutoff
    ]
    print(f"  [INFO] {len(filtered)} posts dentro da janela de {days} dias")
    return filtered


def get_top_posts(posts: list, top_n: int = TOP_N) -> list:
    """
    Calcula o engagement score, ordena e retorna os top N posts.
    """
    for post in posts:
        post["engagement_score"] = calculate_engagement_score(post)

    sorted_posts = sorted(posts, key=lambda p: p["engagement_score"], reverse=True)
    return sorted_posts[:top_n]


def format_post(post: dict) -> dict:
    """
    Extrai apenas os campos relevantes conforme a diretriz.
    """
    created_utc = post.get("created_utc", 0)
    created_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

    return {
        "title": post.get("title", ""),
        "author": post.get("author", "[deleted]"),
        "url": f"https://www.reddit.com{post.get('permalink', '')}",
        "score": post.get("score", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.5),
        "num_comments": post.get("num_comments", 0),
        "engagement_score": round(post.get("engagement_score", 0), 2),
        "created_utc": created_str,
        "flair": post.get("link_flair_text") or "",
    }


def save_results(subreddit: str, top_posts: list) -> Path:
    """
    Salva os resultados em .tmp/top_posts_{subreddit}.json
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"top_posts_{subreddit}.json"

    payload = {
        "subreddit": subreddit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "time_window_days": TIME_WINDOW_DAYS,
        "top_n": TOP_N,
        "posts": [format_post(p) for p in top_posts],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  [SAVED] {output_path}")
    return output_path


def print_summary(subreddit: str, top_posts: list):
    """
    Exibe um resumo legível dos top posts no terminal.
    """
    print(f"\n{'='*60}")
    print(f"  TOP {TOP_N} posts de r/{subreddit} (última semana)")
    print(f"{'='*60}")
    for i, post in enumerate(top_posts, 1):
        p = format_post(post)
        print(f"\n#{i} [{p['engagement_score']} pts] {p['title']}")
        print(f"   Autor    : u/{p['author']}")
        print(f"   Score    : {p['score']} | Comentários: {p['num_comments']} | Ratio: {p['upvote_ratio']}")
        print(f"   Flair    : {p['flair'] or 'N/A'}")
        print(f"   Link     : {p['url']}")
        print(f"   Criado   : {p['created_utc']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n[START] Buscando top {TOP_N} posts da semana em: {', '.join(['r/' + s for s in SUBREDDITS])}")
    print(f"        Janela de tempo: {TIME_WINDOW_DAYS} dias | Posts buscados: {FETCH_LIMIT} por subreddit\n")

    all_results = {}

    for subreddit in SUBREDDITS:
        print(f"\n--- Processando r/{subreddit} ---")

        posts = fetch_posts(subreddit)
        if not posts:
            print(f"  [SKIP] Nenhum post retornado para r/{subreddit}")
            continue

        weekly_posts = filter_by_time_window(posts)
        if not weekly_posts:
            print(f"  [WARN] Nenhum post da última semana em r/{subreddit}")
            continue

        top_posts = get_top_posts(weekly_posts)
        print_summary(subreddit, top_posts)
        output_path = save_results(subreddit, top_posts)

        all_results[subreddit] = str(output_path)

        # Pausa entre requests para ser gentil com a API pública
        time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"[DONE] Resultados salvos em:")
    for sub, path in all_results.items():
        print(f"  r/{sub}: {path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
