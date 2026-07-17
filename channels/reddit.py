import httpx
from .base import Channel

HEADERS = {"User-Agent": "agent-scrapeify/1.0"}


class RedditChannel(Channel):
    name = "reddit"

    def can_handle(self, url: str) -> bool:
        return "reddit.com" in url

    async def fetch(self, url: str) -> dict:
        # Use Jina Reader to get clean text from any Reddit post
        jina_url = f"https://r.jina.ai/{url}"
        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            resp = await client.get(jina_url)
            return {
                "platform": "reddit",
                "url": url,
                "content": resp.text[:3000],
            }

    async def search(self, keyword: str, limit: int = 5) -> list[dict]:
        # Search Reddit via its JSON search API
        search_url = "https://www.reddit.com/search.json"
        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            resp = await client.get(search_url, params={"q": keyword, "limit": limit, "type": "link"})
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            results = []
            for p in posts[:limit]:
                d = p.get("data", {})
                results.append({
                    "platform": "reddit",
                    "title": d.get("title"),
                    "body": d.get("selftext", "")[:500] or d.get("url", ""),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "subreddit": d.get("subreddit"),
                    "score": d.get("score"),
                    "num_comments": d.get("num_comments"),
                })
            return results
