from flask import Flask, render_template

app = Flask(__name__)

# --- Carrega os voos a partir do arquivo listaVoos.text ---
def carregar_voos():
    try:
        with open("/home/cibele/Documentos/TrabalhoFinalED2/arquivos/listaVoos.text", "r", encoding="utf-8") as f:
            conteudo = f.read()
            exec(conteudo, globals())  # Cria a lista Voos
            return globals().get("Voos", [])
    except Exception as e:
        print("Erro ao carregar voos:", e)
        return []


@app.route('/')
def home():
    return "<h1>Bem-vindo(a) ao Sistema de Voos ✈️</h1><p>Acesse <a href='/voos'>/voos</a> para ver a lista completa.</p>"


@app.route('/voos')
def listar_voos():
    voos = carregar_voos()
    return render_template('voos.html', voos=voos)


if __name__ == "__main__":
    voos = carregar_voos()
    print("Lista de voos carregada do arquivo:\n")
    for v in voos:
        print(f"Código: {v['codigo']}, Origem: {v['origem']}, Destino: {v['destino']}, Preço: R$ {v['preco']:.2f}")

    app.run(debug=True)

