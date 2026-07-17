class Channel:
    name: str = ""

    def can_handle(self, url: str) -> bool:
        return False

    async def fetch(self, url: str) -> dict:
        raise NotImplementedError

    async def search(self, keyword: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError
