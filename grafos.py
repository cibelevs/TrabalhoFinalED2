from sistemaVoos import app, carregar_voos
from flask import render_template, request
import networkx as nx
from airportsdata import load
from math import radians, sin, cos, sqrt, atan2
import folium

from folium.plugins import MarkerCluster

# ============================================================
# 1. MAPEAMENTO COMPLETO (CIDADE → IATA)
# ============================================================
IATA_MAP = {
    # BRASIL
    "SALVADOR": "SSA", "SSA": "SSA",
    "SÃO PAULO": "GRU", "SAO PAULO": "GRU", "GRU": "GRU",
    "RIO DE JANEIRO": "GIG", "RIO": "GIG", "GIG": "GIG",

    "FORTALEZA": "FOR", "FOR": "FOR",
    "RECIFE": "REC", "REC": "REC",
    "BRASILIA": "BSB", "BRASÍLIA": "BSB", "BSB": "BSB",
    "BELEM": "BEL", "BELÉM": "BEL", "BEL": "BEL",
    "MANAUS": "MAO", "MAO": "MAO",
    "NATAL": "NAT", "NAT": "NAT",
    "TERESINA": "THE", "THE": "THE",
    "SAO LUIS": "SLZ", "SÃO LUIS": "SLZ", "SLZ": "SLZ",
    "MACEIO": "MCZ", "MACÉIO": "MCZ", "MCZ": "MCZ",
    "FLORIANOPOLIS": "FLN", "FLN": "FLN",
    "PORTO ALEGRE": "POA", "POA": "POA",
    "CURITIBA": "CWB", "CWB": "CWB",
    "VITORIA": "VIX", "VITÓRIA": "VIX", "VIX": "VIX",
    "BELO HORIZONTE": "CNF", "CNF": "CNF",
    "CUIABA": "CGB", "CUIABÁ": "CGB", "CGB": "CGB",
    "GOIANIA": "GYN", "GOIÂNIA": "GYN", "GYN": "GYN",
    "FOZ": "IGU", "FOZ DO IGUAÇU": "IGU", "IGU": "IGU",

    # INTERNACIONAIS
    "MIAMI": "MIA", "MIA": "MIA",
    "ORLANDO": "MCO", "MCO": "MCO",
    "NOVA YORK": "JFK", "JFK": "JFK",
    "PARIS": "CDG", "CDG": "CDG",
    "LISBOA": "LIS", "LIS": "LIS",
    "DUBAI": "DXB", "DXB": "DXB",
    "MADRID": "MAD", "MAD": "MAD",
    "SANTIAGO": "SCL", "SCL": "SCL",
    "BUENOS AIRES": "EZE", "EZE": "EZE",
    "MONTEVIDEO": "MVD", "MVD": "MVD",
    "LONDRES": "LHR", "LHR": "LHR",
}


CIDADE_REAL = {
    "SSA": "Salvador",
    "GRU": "São Paulo",
    "GIG": "Rio de Janeiro",
    "REC": "Recife",
    "FOR": "Fortaleza",
    "BSB": "Brasília",
    "BEL": "Belém",
    "MAO": "Manaus",
    "NAT": "Natal",
    "THE": "Teresina",
    "SLZ": "São Luís",
    "MCZ": "Maceió",
    "FLN": "Florianópolis",
    "POA": "Porto Alegre",
    "CWB": "Curitiba",
    "VIX": "Vitória",
    "CNF": "Belo Horizonte",
    "CGB": "Cuiabá",
    "GYN": "Goiânia",
    "IGU": "Foz do Iguaçu",
    # internacionais se você usar:
    "MIA": "Miami",
    "MCO": "Orlando",
    "JFK": "Nova York",
    "CDG": "Paris",
    "LIS": "Lisboa",
    "MAD": "Madrid",
    "SCL": "Santiago",
}


def nome_cidade(iata):
    nome = CIDADE_REAL.get(iata, iata)
    return f"{nome} ({iata})"



def coordenadas_rota(rota):
    airports = load("IATA")
    coords = []

    for iata in rota:
        info = airports.get(iata)
        if info:
            coords.append([info["lat"], info["lon"]])

    return coords




# ============================================================
# 2. Função para normalizar o nome e obter o IATA
# ============================================================
def normalizar_iata(valor):
    if not valor:
        return None
    valor = valor.strip().upper()
    return IATA_MAP.get(valor, None)


# ============================================================
# 3. Distância Haversine
# ============================================================
def distancia(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ============================================================
# 4. Gerar o grafo redes de rotas
# ============================================================
def gerar_grafo_rotas():
    voos = carregar_voos()
    airports = load("IATA")
    G = nx.Graph()

    for v in voos:
        origem = normalizar_iata(v["origem"])
        destino = normalizar_iata(v["destino"])

        if not origem or not destino:
            print("⚠ Ignorando voo com cidade desconhecida:", v)
            continue

        o = airports.get(origem)
        d = airports.get(destino)

        if not o or not d:
            print("⚠ IATA não encontrado:", origem, destino)
            continue

        dist = distancia(o["lat"], o["lon"], d["lat"], d["lon"])

        G.add_edge(
            origem,
            destino,
            peso=dist,
            preco=v["preco"],
            codigo=v["codigo"]
        )

    return G


# ============================================================
# 5. Página tabela de rotas
# ============================================================
@app.route("/grafo_rotas")
def grafo_rotas():
    G = gerar_grafo_rotas()
    dados = list(G.edges(data=True))
    return render_template("grafo.html", edges=dados, nome_cidade=nome_cidade)




# ============================================================
# 6. Melhor rota entre dois pontos
# ============================================================





@app.route("/melhor_rota", methods=["GET", "POST"])
def melhor_rota():
    rota = []
    dist = None
    erro = None
    coords = None   # <---- adicionar isso

    if request.method == "POST":
        origem = normalizar_iata(request.form["origem"])
        destino = normalizar_iata(request.form["destino"])

        if not origem or not destino:
            erro = "Cidade ou código IATA inválido."
        else:
            G = gerar_grafo_rotas()
            try:
                rota = nx.shortest_path(G, origem, destino, weight="peso")
                dist = nx.shortest_path_length(G, origem, destino, weight="peso")
                
                # ★★★ PEGAR COORDENADAS AQUI ★★★
                coords = coordenadas_rota(rota)

            except nx.NetworkXNoPath:
                erro = "Nenhuma rota encontrada."

    return render_template("rota.html", rota=rota, dist=dist, erro=erro, coords=coords)



@app.route("/todas_rotas", methods=["GET", "POST"])
def todas_rotas():
    erro = None
    mapa = None

    if request.method == "POST":
        origem = normalizar_iata(request.form["origem"])
        destino = normalizar_iata(request.form["destino"])

        if not origem or not destino:
            erro = "Cidade ou código IATA inválido."
        else:
            G = gerar_grafo_rotas()

            try:
                caminhos = list(nx.all_simple_paths(G, origem, destino))

                if not caminhos:
                    erro = "Nenhum caminho encontrado."
                else:
                    airports = load("IATA")
                    mapa = folium.Map(location=[-15, -50], zoom_start=4)

                    cores = ["red", "blue", "green", "purple", "orange", "black"]

                    # Desenhar cada caminho
                    for i, path in enumerate(caminhos):
                        coords = coordenadas_rota(path)

                        folium.PolyLine(
                            coords,
                            weight=4,
                            opacity=0.8,
                            color=cores[i % len(cores)],
                            tooltip=" → ".join(path)
                        ).add_to(mapa)

                    # Adicionar marcadores dos aeroportos
                    for codigo in G.nodes():
                        info = airports.get(codigo)
                        if info:
                            folium.Marker(
                                [info["lat"], info["lon"]],
                                popup=codigo
                            ).add_to(mapa)

                    mapa.save("static/todas_rotas.html")

            except nx.NetworkXNoPath:
                erro = "Não existe rota entre esses aeroportos."

    return render_template("todas_rotas.html", erro=erro, mapa=mapa)



# ============================================================
# 7. Mapa REAL com aeroportos e rotas
# ============================================================
@app.route("/grafo_imagem")
def grafo_imagem():
    G = gerar_grafo_rotas()
    airports = load("IATA")

    mapa = folium.Map(location=[-15, -50], zoom_start=4)
    cluster = MarkerCluster().add_to(mapa)

    # Adiciona nós
    for codigo in G.nodes():
        info = airports.get(codigo)
        if not info:
            continue

        folium.Marker(
            location=[info["lat"], info["lon"]],
            tooltip=codigo,
            popup=f"Aeroporto: {codigo}"
        ).add_to(cluster)

    # Adiciona linhas entre nós (arestas)
    for u, v, dados in G.edges(data=True):
        info_u = airports.get(u)
        info_v = airports.get(v)
        if not info_u or not info_v:
            continue

        folium.PolyLine(
            [(info_u["lat"], info_u["lon"]),
             (info_v["lat"], info_v["lon"])],
            tooltip=f"{dados['peso']:.1f} km",
            color="blue",
            weight=3
        ).add_to(mapa)
        

    mapa.save("static/grafo_mapa.html")
    return '<iframe src="/static/grafo_mapa.html" width="100%" height="800px"></iframe>'


# ============================================================
# 8. Main
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
