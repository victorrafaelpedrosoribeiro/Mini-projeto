import re
import time

import requests
from bs4 import BeautifulSoup


URL = "https://store.steampowered.com/search/results/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}

JOGOS_POR_PAGINA = 50
MAX_PAGINAS = 3  


def buscar_html(inicio=0):
    """Busca uma 'página' de resultados e devolve o HTML dos jogos."""
    params = {
        "specials": 1,        # só jogos em promoção
        "cc": "br",           # loja do Brasil (preços em R$)
        "l": "portuguese",
        "start": inicio,
        "count": JOGOS_POR_PAGINA,
        "infinite": 1,        # faz o servidor responder em JSON
        "category1": 998,     # só jogos (sem DLCs, trilhas, etc.)
    }
    try:
        resposta = requests.get(URL, params=params, headers=HEADERS, timeout=15)
        resposta.raise_for_status()
        return resposta.json().get("results_html", "")
    except (requests.RequestException, ValueError) as erro:
        print(f"Erro ao acessar a Steam: {erro}")
        return None


def extrair_promocoes(html):
    soup = BeautifulSoup(html, "html.parser")
    promocoes = []

    for jogo in soup.select("a.search_result_row"):
        titulo = jogo.select_one(".title")
        desconto = jogo.select_one(".discount_pct")
        preco_final = jogo.select_one(".discount_final_price")
        preco_original = jogo.select_one(".discount_original_price")

        # Se não tem desconto ou preço, não é uma promoção válida
        if not (titulo and desconto and preco_final):
            continue

        desconto_encontrado = re.search(r"-\d+%", desconto.get_text(strip=True))
        preco_encontrado = re.search(r"R\$\s?[\d.]*\d,\d{2}", preco_final.get_text(strip=True))
        if not (desconto_encontrado and preco_encontrado):
            continue

        original_encontrado = None
        if preco_original:
            original_encontrado = re.search(
                r"R\$\s?[\d.]*\d,\d{2}", preco_original.get_text(strip=True)
            )

        promocoes.append({
            "nome": titulo.get_text(strip=True),
            "preco": preco_encontrado.group(0),
            "preco_original": original_encontrado.group(0) if original_encontrado else "",
            "desconto": desconto_encontrado.group(0),
            "link": jogo.get("href", "").split("?")[0],
        })

    return promocoes


def mostrar_promocoes(promocoes):
    if not promocoes:
        print("Nenhuma promoção encontrada (ou não foi possível ler a página).")
        return

    print(f"=== {len(promocoes)} promoções encontradas na Steam (em R$) ===\n")
    for jogo in promocoes:
        print(jogo["nome"])
        if jogo["preco_original"]:
            print(f"{jogo['preco_original']} -> {jogo['preco']} ({jogo['desconto']})")
        else:
            print(f"{jogo['preco']} ({jogo['desconto']})")
        print(jogo["link"])
        print()


def main():
    todas = []
    links_ja_vistos = set()

    for pagina in range(MAX_PAGINAS):
        html = buscar_html(inicio=pagina * JOGOS_POR_PAGINA)

        if html is None:
            break
        if not html.strip():
            break  # acabaram os resultados

        for promo in extrair_promocoes(html):
            if promo["link"] not in links_ja_vistos:
                links_ja_vistos.add(promo["link"])
                todas.append(promo)

        time.sleep(1) 

    mostrar_promocoes(todas)


if __name__ == "__main__":
    main()
