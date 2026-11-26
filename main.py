import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")

@app.get("/search")
async def search_goofish(q: str):
    try:
        # 1. Chamada direta via HTTP para a API da Apify (sem usar a biblioteca client)
        # Isso evita o erro de 'Run object is not subscriptable'
        url = f"https://api.apify.com/v2/acts/unitbytes~goofish-xianyu-search-scraper/runs?token={APIFY_TOKEN}"
        
        payload = {
            "keyword": q,
            "maxItems": 20,
            "detailLevel": "full",
        }
        
        # Inicia a busca
        response = requests.post(url, json=payload).json()
        run_id = response.get("data", {}).get("id")
        dataset_id = response.get("data", {}).get("defaultDatasetId")

        if not dataset_id:
            raise Exception("Não foi possível iniciar a busca no Goofish.")

        # 2. Busca os itens do dataset
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
        items_response = requests.get(dataset_url).json()

        results = []
        for item in items_response:
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
