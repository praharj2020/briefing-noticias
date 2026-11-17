#!/usr/bin/env python3
"""Vai buscar notícias do Brasil e do Rio de Janeiro à API GNews e escreve JSON.
Uso: GNEWS_API_KEY=... python3 tools/gnews_fetch.py /caminho/saida.json
A chave NUNCA deve ser guardada no repositório."""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("GNEWS_API_KEY", "").strip()
if not KEY:
    sys.exit("GNEWS_API_KEY em falta")
OUT = sys.argv[1] if len(sys.argv) > 1 else "gnews.json"
PREF = ["folha.uol.com.br", "estadao.com.br", "oglobo.globo.com", "valor.globo.com", "valor.com.br"]
FROM = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
BLOCK = ["instagram.com", "facebook.com", "youtube.com", "cmjornal.pt", "cnnportugal.iol.pt", "theportugalnews.com", "lusa.pt"]

QUERIES = [  # (rotulo, endpoint, parametros)
    ("brasil_top", "top-headlines", {"category": "general", "country": "br", "lang": "pt", "max": 10}),
    ("negocios_top", "top-headlines", {"category": "business", "country": "br", "lang": "pt", "max": 10}),
    ("rio", "search", {"q": '"Rio de Janeiro"', "country": "br", "lang": "pt", "from": FROM, "sortby": "publishedAt", "max": 10}),
    ("folha", "search", {"q": "Folha de S.Paulo OR Folha", "country": "br", "lang": "pt", "from": FROM, "max": 10}),
    ("estadao", "search", {"q": "Estadão OR Estado de S. Paulo", "country": "br", "lang": "pt", "from": FROM, "max": 10}),
    ("oglobo", "search", {"q": "O Globo", "country": "br", "lang": "pt", "from": FROM, "max": 10}),
    ("valor", "search", {"q": "Valor Econômico", "country": "br", "lang": "pt", "from": FROM, "max": 10}),
]

def call(endpoint, params):
    p = dict(params, apikey=KEY)
    url = f"https://gnews.io/api/v4/{endpoint}?{urllib.parse.urlencode(p)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

res, seen, erros = {}, set(), []
for label, ep, params in QUERIES:
    try:
        data = call(ep, params)
    except Exception as e:
        erros.append(f"{label}: {e}")
        continue
    itens = []
    for a in data.get("articles", []):
        u = a.get("url", "")
        dom = urllib.parse.urlparse(u).netloc.lower()
        if not u.startswith("https://") or any(b in dom for b in BLOCK) or u in seen:
            continue
        seen.add(u)
        itens.append({"titulo": a.get("title"), "descricao": a.get("description"), "url": u,
                      "publicado": a.get("publishedAt"), "fonte": (a.get("source") or {}).get("name"),
                      "dominio": dom, "preferido": any(dom.endswith(d) for d in PREF)})
    res[label] = itens
    time.sleep(1.1)  # respeitar limites por segundo

json.dump({"gerado": datetime.now(timezone.utc).isoformat(), "erros": erros, "resultados": res},
          open(OUT, "w"), ensure_ascii=False, indent=1)
print(f"{sum(len(v) for v in res.values())} artigos, {len(erros)} erros -> {OUT}")
