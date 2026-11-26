import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apify_client import ApifyClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
client = ApifyClient(APIFY_TOKEN)

@app.get("/search")
async def search_goofish(q: str):
    try:
        run_input = {
            "keyword": q,
            "maxItems": 20,
            "detailLevel": "full",
        }

        # CORREÇÃO AQUI: Chamamos o actor e pegamos o ID do dataset corretamente
        run = client.actor("unitbytes/goofish-xianyu-search-scraper").call(run_input=run_input)
        
        # Em versões novas, usamos run['defaultDatasetId'] ou run.default_dataset_id
        dataset_id = run.get("defaultDatasetId") if isinstance(run, dict) else run["defaultDatasetId"]
        
        items = list(client.dataset(dataset_id).iterate_items())

        results = []
        for item in items:
            results.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "price": item.get("price"),
                "url": item.get("url"),
                "img": item.get("image") or "https://via.placeholder.com/200",
                "condition": item.get("condition", "Usado")
            })

        return {"status": "success", "data": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro técnico: {str(e)}")
