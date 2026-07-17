from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from channels import ALL_CHANNELS

load_dotenv()

app = FastAPI(title="Agent Scrapeify", version="1.0.0")


class FetchRequest(BaseModel):
    url: str


class SearchRequest(BaseModel):
    keyword: str
    platforms: list[str] = ["youtube", "reddit", "twitter"]
    limit: int = 5


@app.get("/")
def root():
    return {"name": "Agent Scrapeify", "status": "running", "platforms": ["youtube", "reddit", "twitter"]}


@app.post("/fetch")
async def fetch(req: FetchRequest):
    for channel in ALL_CHANNELS:
        if channel.can_handle(req.url):
            try:
                result = await channel.fetch(req.url)
                return {"success": True, "data": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=400, detail="No channel can handle this URL")


@app.post("/search")
async def search(req: SearchRequest):
    results = []
    for channel in ALL_CHANNELS:
        if channel.name in req.platforms:
            try:
                data = await channel.search(req.keyword, limit=req.limit)
                results.extend(data)
            except Exception as e:
                results.append({"platform": channel.name, "error": str(e)})
    return {"success": True, "keyword": req.keyword, "results": results}
