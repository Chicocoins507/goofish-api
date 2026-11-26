import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apify_client import ApifyClient

app = FastAPI()

# Permite que o seu site converse com o servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# O Token será configurado depois no Render para ficar seguro
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
client = ApifyClient(APIFY_TOKEN)

@app.get("/search")
async def search_goofish(q: str):
    try:
        # Usa o robô da Apify especializado em buscas do Goofish
        run_input = {
            "keyword": q,
            "maxItems": 20,
            "detailLevel": "full",
        }

        run = client.actor("unitbytes/goofish-xianyu-search-scraper").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

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
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
