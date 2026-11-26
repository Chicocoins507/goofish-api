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

        # Executa o ator
        run_obj = client.actor("unitbytes/goofish-xianyu-search-scraper").call(run_input=run_input)
        
        # FORÇA a conversão do objeto para dicionário para evitar o erro 'not subscriptable'
        if not isinstance(run_obj, dict):
            run_data = vars(run_obj)
        else:
            run_data = run_obj

        dataset_id = run_data.get("defaultDatasetId")

        if not dataset_id:
            raise Exception("ID do dataset não encontrado no retorno da API.")

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
