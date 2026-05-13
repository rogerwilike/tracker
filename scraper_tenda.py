import time
import unicodedata
import requests
from pprint import pprint
import sqlite3
from datetime import datetime

API_LOCAL = "http://127.0.0.1:8000"
ID_TENDA = 4

BASE_URL = "https://api.tendaatacado.com.br/api/public/store/search"

PRODUTOS_MONITORADOS = {
    "arroz": 1,
    "feijao": 2,
    "leite": 3,
    "oleo": 4,
    "acucar": 5,
    "chocolate": 6,
}

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "pt-BR,pt;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "authorization": "Bearer 03b2184b6d9d36b7d9310fd5d2b9fd35",
    "cache-control": "no-cache",
    "desktop-platform": "true",
    "origin": "https://www.tendaatacado.com.br",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.tendaatacado.com.br/",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
}

COOKIES = {
    "az_asm": "Kp62Lan3bhikIavNz2SINPhbYGhhGRXw0drrQfXJThAF5Hc1gctyghMM6zhMqdlZrzv0mu02gOyLxJFq",
    "az_botm": "dfa8e5df8ecd3abf36be2377adba9436",
    "_evga_6a21": '{"uuid":"2191ed2c5f012ab7"}',
    "_sfid_6c6b": '{"anonymousId":"2191ed2c5f012ab7","consents":[{"consent":{"purpose":"Personalization","provider":"tendaatacado.com.br","status":"Opt In"},"lastUpdateTime":"2026-04-13T14:06:35.048Z","lastSentTime":"2026-04-13T14:06:35.051Z"}]}',
    "_gid": "GA1.3.541076949.1776089200",
    "_gcl_au": "1.1.1493928834.1776089200",
    "_clck": "bvzgap%5E2%5Eg56%5E0%5E2294",
    "_hjSessionUser_1377533": "eyJpZCI6ImQzOWIxMTNiLTFjZGItNWVjNS05OTZjLTZkYzdmZmRkMWQzYyIsImNyZWF0ZWQiOjE3NzYwODkyMDA1NTYsImV4aXN0aW5nIjp0cnVlfQ==",
    "_hjSession_1377533": "eyJpZCI6ImQyNDlhNTZjLTNjNzgtNDQzOC1iNzE1LTMyNjRiNTljNzcxYyIsImMiOjE3NzYwOTUyMzkyMTEsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=",
    "_uetsid": "fe90dd90374111f183041f3c43b24778",
    "_uetvid": "fe910b70374111f185174b19733c8403",
    "_uetmsclkid": "_uetb1240587f865192a03586c5b000314f5",
    "_ga": "GA1.3.1766902160.1776089200",
    "JSESSIONID": "D3931B9087A4C444BE51BA2922036F1A",
    "_ga_G05J2RCJLS": "GS2.1.s1776095240$o2$g1$t1776097455$j19$l0$h0",
    "_clsk": "f781b2%5E1776097839162%5E11%5E1%5Ed.clarity.ms%2Fcollect",
}

def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower().strip()

def extrair_produtos(data):
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in [
        "products",
        "items",
        "results",
        "hits",
        "data",
        "content",
        "productsList",
        "searchResults",
        "store_products",
    ]:
        value = data.get(key)
        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            for subkey in ["products", "items", "results", "hits", "content"]:
                subvalue = value.get(subkey)
                if isinstance(subvalue, list):
                    return subvalue

    return []

def pegar_nome(item):
    if not isinstance(item, dict):
        return ""

    candidatos = [
        item.get("name"),
        item.get("title"),
        item.get("description"),
    ]

    detail = item.get("detail")
    if isinstance(detail, dict):
        candidatos.extend([
            detail.get("name"),
            detail.get("title"),
            detail.get("description"),
        ])

    for c in candidatos:
        if c:
            return str(c)

    return ""

def pegar_preco(item):
    if not isinstance(item, dict):
        return None

    candidatos = [
        item.get("price"),
        item.get("salePrice"),
        item.get("bestPrice"),
        item.get("currentPrice"),
    ]

    price = item.get("price")
    if isinstance(price, dict):
        for k in ["value", "amount", "price", "current"]:
            if price.get(k) is not None:
                candidatos.insert(0, price.get(k))
                break

    detail = item.get("detail")
    if isinstance(detail, dict):
        candidatos.extend([
            detail.get("price"),
            detail.get("salePrice"),
            detail.get("bestPrice"),
        ])
        dprice = detail.get("price")
        if isinstance(dprice, dict):
            for k in ["value", "amount", "price", "current"]:
                if dprice.get(k) is not None:
                    candidatos.insert(0, dprice.get(k))
                    break

    for c in candidatos:
        if isinstance(c, (int, float)):
            return float(c)
        if isinstance(c, str):
            txt = c.replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                return float(txt)
            except:
                pass

    return None

def pegar_imagem(item):
    if not isinstance(item, dict):
        return None

    candidatos = [
        item.get("image"),
        item.get("thumbnail"),
        item.get("imageUrl"),
        item.get("image_url"),
    ]

    detail = item.get("detail")
    if isinstance(detail, dict):
        candidatos.extend([
            detail.get("image"),
            detail.get("thumbnail"),
            detail.get("imageUrl"),
            detail.get("image_url"),
        ])

        images = detail.get("images")
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                for k in ["url", "src", "thumbnail"]:
                    if first.get(k):
                        return first.get(k)
            elif isinstance(first, str):
                return first

    images = item.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            for k in ["url", "src", "thumbnail"]:
                if first.get(k):
                    return first.get(k)
        elif isinstance(first, str):
            return first

    for c in candidatos:
        if c:
            return c

    return None

def enviar_para_api(id_produto, id_mercado, preco, nome_completo, imagem_url=None):
    # O arquivo pricetracker.db deve estar na mesma pasta no GitHub
    db_path = "pricetracker.db" 
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ajuste os nomes das colunas 'produto_id', 'estabelecimento_id', etc., 
        # conforme a estrutura real da sua tabela no SQLite
        sql = """
        INSERT INTO registros_precos (produto_id, estabelecimento_id, preco, data_coleta, nome_detalhado, imagem_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(sql, (id_produto, id_mercado, preco, data_hoje, nome_completo, imagem_url))
        
        conn.commit()
        conn.close()
        print(f"    ✅ Banco atualizado: {nome_completo[:30]}...")
    except Exception as e:
        print(f"    ❌ Erro ao salvar no SQLite: {e}")

def buscar_tenda():
    print("-" * 70)
    print("🚀 PRICE TRACKER - TENDA PIRACICABA (API CORRIGIDA)")
    print("-" * 70)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    for termo, id_produto in PRODUTOS_MONITORADOS.items():
        print(f"\n🔍 Pesquisando: {termo}...")

        total_salvos = 0
        termo_norm = normalizar(termo)

        for pagina in range(1, 6):
            params = {
                "query": termo,
                "page": pagina,
                "order": "relevance",
                "save": "true",
                "cartId": "34958565",
            }

            try:
                resp = session.get(BASE_URL, params=params, timeout=20)

                if resp.status_code != 200:
                    print(f"  ❌ HTTP {resp.status_code} na página {pagina}")
                    print(f"  ↳ Resposta: {resp.text[:300]}")
                    break

                try:
                    data = resp.json()
                except Exception:
                    print(f"  ❌ Resposta não é JSON na página {pagina}")
                    print(resp.text[:500])
                    break

                produtos = extrair_produtos(data)

                if pagina == 1:
                    if isinstance(data, dict):
                        print(f"  ℹ️ Chaves da resposta: {list(data.keys())[:20]}")
                    print(f"  📦 Itens brutos encontrados: {len(produtos)}")

                if not produtos:
                    break

                for item in produtos:
                    nome = pegar_nome(item)
                    preco = pegar_preco(item)
                    imagem = pegar_imagem(item)

                    if not nome or preco is None:
                        continue

                    nome_norm = normalizar(nome)

                    if termo_norm in nome_norm or any(p in nome_norm for p in termo_norm.split()):
                        print(f"  ✅ {nome[:80]} | R$ {preco:.2f}")
                        enviar_para_api(id_produto, ID_TENDA, preco, nome, imagem)
                        total_salvos += 1

                time.sleep(1)

            except requests.RequestException as e:
                print(f"  ❌ Erro na requisição: {e}")
                break
            except Exception as e:
                print(f"  ❌ Erro inesperado: {e}")
                break

        if total_salvos == 0:
            print(f"  ⚠️ Nenhum {termo} relevante encontrado.")
        else:
            print(f"  📦 Sucesso! {total_salvos} itens salvos.")

        time.sleep(2)

if __name__ == "__main__":
    buscar_tenda()
    print("\n" + "=" * 70)
    input("Coleta finalizada. Pressione ENTER para fechar...")