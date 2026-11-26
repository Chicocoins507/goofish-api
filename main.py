import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apify_client import ApifyClient
from typing import List, Dict

app = FastAPI()

# Configuração de CORS para permitir que seu frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações da Apify
APIFY_TOKEN = os.getenv("APIFY_TOKEN") # Certifique-se de ter essa variável no Render
client = ApifyClient(APIFY_TOKEN)

# Dicionário de Cache: { "termo_de_busca": {"timestamp": 12345, "data": [...]} }
cache = {}
CACHE_EXPIRATION = 1800  # 30 minutos em segundos

@app.get("/search")
async def search(q: str):
    if not q:
        raise HTTPException(status_code=400, detail="O termo de busca é obrigatório")

    # 1. Verificar se o resultado está no cache e se ainda é válido
    current_time = time.time()
    if q in cache:
        cached_data = cache[q]
        if current_time - cached_data["timestamp"] < CACHE_EXPIRATION:
            print(f"Retornando resultado do cache para: {q}")
            return {"status": "success", "data": cached_data["data"], "source": "cache"}

    try:
        print(f"Iniciando busca real na Apify para: {q}")
        # 2. Chamar o Actor da Apify
        run_input = {
            "search": q,
            "maxItems": 20,
        }
        
        # Executa o scraper e aguarda a conclusão
        run = client.actor("unitbytes/goofish-xianyu-search-scraper").call(run_input=run_input)
        
        # 3. Extrair os dados do dataset
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        results = []
        for item in dataset_items:
            results.append({
                "id": item.get("id") or item.get("item_id"),
                "title": item.get("title"),
                "price": item.get("price"),
                "img": item.get("image"),
                "url": item.get("url"),
                "condition": item.get("condition")
            })

        # 4. Salvar no cache antes de retornar
        cache[q] = {
            "timestamp": current_time,
            "data": results
        }

        return {"status": "success", "data": results, "source": "api"}

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar busca: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "online", "cache_size": len(cache)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
