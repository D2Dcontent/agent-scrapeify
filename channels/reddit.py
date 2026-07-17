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
        # Search Reddit via Jina Reader + DuckDuckGo (no API key needed)
        query = keyword.replace(" ", "+") + "+site:reddit.com"
        search_url = f"https://r.jina.ai/https://duckduckgo.com/?q={query}&ia=web"
        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            resp = await client.get(search_url)
            return [
                {
                    "platform": "reddit",
                    "keyword": keyword,
                    "content": resp.text[:3000],
                    "note": "Reddit search results via DuckDuckGo + Jina Reader",
                }
            ]
