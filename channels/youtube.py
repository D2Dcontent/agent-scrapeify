import yt_dlp
import httpx
from .base import Channel


class YouTubeChannel(Channel):
    name = "youtube"

    def can_handle(self, url: str) -> bool:
        return "youtube.com" in url or "youtu.be" in url

    async def fetch(self, url: str) -> dict:
        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitlesformat": "json3",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            transcript = ""
            if info.get("subtitles") or info.get("automatic_captions"):
                captions = info.get("automatic_captions", {})
                en = captions.get("en", [])
                if en:
                    cap_url = en[0]["url"]
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(cap_url)
                        data = resp.json()
                        transcript = " ".join(
                            event.get("segs", [{}])[0].get("utf8", "")
                            for event in data.get("events", [])
                            if event.get("segs")
                        )
            return {
                "platform": "youtube",
                "url": url,
                "title": info.get("title", ""),
                "description": info.get("description", "")[:500],
                "transcript": transcript[:3000],
                "views": info.get("view_count"),
                "channel": info.get("uploader"),
            }

    async def search(self, keyword: str, limit: int = 5) -> list[dict]:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{limit}:{keyword}", download=False)
            entries = results.get("entries", [])
            return [
                {
                    "platform": "youtube",
                    "title": e.get("title"),
                    "url": f"https://youtube.com/watch?v={e.get('id')}",
                    "views": e.get("view_count"),
                    "channel": e.get("uploader"),
                    "duration": e.get("duration"),
                }
                for e in entries
            ]
