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

            # Extract tweets from nested entries structure
            results = []
            try:
                top = data.get("entries", []) or []
                for section in top:
                    for entry in section.get("entries", []):
                        content = entry.get("content", {})
                        item_content = content.get("itemContent", {}) or content.get("content", {}).get("itemContent", {})
                        tweet_results = item_content.get("tweet_results", {})
                        result = tweet_results.get("result", {})
                        legacy = result.get("legacy", {})
                        if not legacy:
                            continue
                        tweet_id = legacy.get("id_str") or result.get("rest_id", "")
                        user = result.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
                        results.append({
                            "platform": "twitter",
                            "text": legacy.get("full_text", "")[:280],
                            "username": user.get("screen_name"),
                            "url": f"https://twitter.com/i/web/status/{tweet_id}" if tweet_id else "",
                            "likes": legacy.get("favorite_count"),
                            "retweets": legacy.get("retweet_count"),
                        })
                        if len(results) >= limit:
                            break
                    if len(results) >= limit:
                        break
            except Exception as e:
                return [{"platform": "twitter", "error": f"Parse error: {str(e)[:200]}"}]

            if not results:
                return [{"platform": "twitter", "error": f"No tweets found. Raw keys: {list(data.keys())}"}]
            return results
