import os
import httpx
from .base import Channel

RAPIDAPI_HOST = "twitter-aio.p.rapidapi.com"

def _headers():
    return {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", ""),
        "x-rapidapi-host": RAPIDAPI_HOST,
    }


class TwitterChannel(Channel):
    name = "twitter"

    def can_handle(self, url: str) -> bool:
        return "twitter.com" in url or "x.com" in url

    async def fetch(self, url: str) -> dict:
        tweet_id = url.rstrip("/").split("/")[-1].split("?")[0]
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://{RAPIDAPI_HOST}/tweet/{tweet_id}",
                headers=_headers(),
            )
            data = resp.json()
            tweet = data.get("data", {})
            return {
                "platform": "twitter",
                "url": url,
                "text": tweet.get("text"),
                "author": tweet.get("author_id"),
                "created_at": tweet.get("created_at"),
                "likes": tweet.get("public_metrics", {}).get("like_count"),
                "retweets": tweet.get("public_metrics", {}).get("retweet_count"),
            }

    async def search(self, keyword: str, limit: int = 5) -> list[dict]:
        # Use Jina Reader + DuckDuckGo to find tweets (free, no API key needed)
        query = keyword.replace(" ", "+") + "+site:twitter.com OR site:x.com"
        search_url = f"https://r.jina.ai/https://duckduckgo.com/?q={query}&ia=web"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/plain",
        }
        async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as client:
            resp = await client.get(search_url)
            lines = [l.strip() for l in resp.text.splitlines() if l.strip()]
            results = []
            for line in lines:
                if ("twitter.com/" in line or "x.com/") and len(line) > 30 and not line.startswith("http"):
                    title = line.lstrip("#*").strip()[:200]
                    results.append({
                        "platform": "twitter",
                        "text": title,
                        "url": f"https://x.com/search?q={keyword.replace(' ', '%20')}",
                    })
                    if len(results) >= limit:
                        break
            if not results:
                results.append({
                    "platform": "twitter",
                    "text": f"Tweets about: {keyword}",
                    "url": f"https://x.com/search?q={keyword.replace(' ', '%20')}",
                    "body": "Click Open to view tweets on X/Twitter",
                })
            return results
