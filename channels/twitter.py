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
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://{RAPIDAPI_HOST}/search",
                headers=_headers(),
                params={"query": keyword, "count": str(limit)},
            )
            data = resp.json()
            if not isinstance(data, dict):
                return [{"platform": "twitter", "error": f"Unexpected response: {str(data)[:200]}"}]
            tweets = data.get("data", []) or []
            if not tweets:
                msg = data.get("message") or data.get("error") or "No results"
                return [{"platform": "twitter", "error": msg}]
            return [
                {
                    "platform": "twitter",
                    "text": t.get("text"),
                    "tweet_id": t.get("id"),
                    "url": f"https://twitter.com/i/web/status/{t.get('id')}",
                    "likes": t.get("public_metrics", {}).get("like_count"),
                    "retweets": t.get("public_metrics", {}).get("retweet_count"),
                }
                for t in tweets
            ]
