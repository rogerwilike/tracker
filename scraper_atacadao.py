import requests
import json
import time
from datetime import datetime
import sqlite3

SESSION = requests.Session()

BASE_URL    = "https://www.atacadao.com.br/api/graphql"
API_LOCAL   = "http://127.0.0.1:8000"
ID_ATACADAO = 1

HEADERS = {
    "accept": "*/*",
    "accept-language": "pt-BR,pt;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "referer": "https://www.atacadao.com.br/",
}

COOKIES = {
    "cf_clearance": "fwJgj4t_wnWFRZjrVAYr8akGsdl5097eaMChvC.8Yto-1775613170-1.2.1.1-57juDXtY6rldIZHiJGUn9rjr31gogDGsp2ZU2F4_lQGPDv6SnxyG2rs9u3SG_cp1OOlRLuCO23XjpP.meJqUmdR9TS0ZOmR_g.Wg_R5Vca93otvrW84jyh9nboidgH9Z6KaU..Lnx1oGvgSuOBQmOXW9vLoIRfIWMP36l1wMba7abzdhWIg3j2laxM3RyWDubAMjTRFv36jCB.vrLlvw5YVI0x..nYQmUdZezZMVls59f14MT0kMjYlkb1xsJEoSK7PFyx2Eb4Kc8NsnGi3RIHbkhsTEf2H_OcxKcv0ahOr1krwL6Xd8TvQ2r0XKL8AmO1ChjXIB9F86TnzwHaVYXA",
    "__cf_bm": "_UFIPhQZKqq_8JIxPbZzrbYk6SEZnoDICgPTciK6Umc-1775613170.142166-1.0.1.1-XAI45zbXorUvHNx71bKBEPwOjL1UfI6dcudIDybwZ41HrivyKvE7V3MZ4uTGAZZ6F8GHokYcutkr3XJO7NX8_nAn3KGVP5nlJvjujPqOqB_SXuw4yNobrCqAr8Js35x9",
    "regionalization": '{"salesChannel":"1","postalCode":"02170-901","seller":"atacadaobr60"}',
}


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


def buscar_atacadao(termo, id_no_banco):
    print(f"\n🔍 Buscando '{termo}'...")

    variables = {
        "first": 15,
        "after": "0",
        "sort": "score_desc",
        "term": termo,
        "selectedFacets": [
            {"key": "channel", "value": "{\"salesChannel\":\"1\",\"seller\":\"atacadaobr60\",\"regionId\":\"U1cjYXRhY2FkYW9icjYw\"}"},
            {"key": "locale",  "value": "pt-BR"}
        ]
    }

    params = {
        "operationName": "ProductsQuery",
        "variables": json.dumps(variables, separators=(",", ":"))
    }

    for tentativa in range(3):
        try:
            resp = SESSION.get(BASE_URL, headers=HEADERS, cookies=COOKIES, params=params, timeout=40)
            break
        except requests.exceptions.ReadTimeout:
            print(f"  ⏳ Timeout! Tentativa {tentativa+1}/3... aguardando 10s")
            time.sleep(10)
    else:
        print(f"❌ Falhou após 3 tentativas. Pulando '{termo}'.")
        return

    if resp.status_code != 200:
        print(f"❌ Erro HTTP {resp.status_code}. Atualize os cookies.")
        return

    edges = (
        resp.json()
            .get("data", {})
            .get("search", {})
            .get("products", {})
            .get("edges", [])
    )

    if not edges:
        print("⚠️ Nenhum produto encontrado.")
        return

    total = 0
    for edge in edges:
        node  = edge.get("node", {})
        nome  = node.get("name")
        preco = node.get("offers", {}).get("lowPrice")

        # Captura imagem
        imagens  = node.get("image", [])
        img_url  = imagens[0].get("url") if imagens else None

        if nome and preco:
            print(f"  🛒 {nome[:50]} | R$ {preco:.2f}")
            enviar_para_api(id_no_banco, ID_ATACADAO, preco, nome, img_url)
            total += 1
            time.sleep(0.2)

    print(f"  📦 {total} itens salvos para '{termo}'")


if __name__ == "__main__":
    print("-" * 55)
    print("  PRICE TRACKER - COLETA ATACADÃO")
    print(f"  Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 55)

    buscar_atacadao("arroz",  id_no_banco=1)
    buscar_atacadao("feijao", id_no_banco=2)
    buscar_atacadao("leite",  id_no_banco=3)
    buscar_atacadao("oleo",   id_no_banco=4)
    buscar_atacadao("acucar", id_no_banco=5)

    print("\n" + "-" * 55)
    print("  COLETA FINALIZADA!")
    print(f"  Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 55)