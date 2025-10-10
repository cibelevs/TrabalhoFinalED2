from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- Carrega os voos a partir do arquivo listaVoos.text ---
def carregar_voos():
    try:
        with open("listaVoos.text", "r", encoding="utf-8") as f:
            conteudo = f.read()
            exec(conteudo, globals())  # Executa o conteúdo (cria a lista Voos)
            return globals().get("Voos", [])
    except Exception as e:
        print(f"Erro ao carregar voos: {e}")
        return []

# --- Página inicial (login do usuário) ---
@app.route('/')
def home():
        return render_template('menu.html')


@app.route('/usuario')
def tela_usuario():
    # Certifique-se de que o template 'usuario.html' existe na pasta 'templates'
    return render_template('usuario.html')


# --- Processa o login ---
@app.route("/login", methods=["POST"])
def login():
    nome = request.form.get("nome")
    senha = request.form.get("senha")

    # Login simples (pode mudar depois para BD)
    if nome == "admin" and senha == "123":
        return redirect(url_for("painel_admin"))
    else:
        return "<h3 style='color:red; text-align:center;'>Usuário ou senha incorretos!</h3><a href='/'>Voltar</a>"

# --- Página do painel administrativo ---
@app.route("/painel")
def painel_admin():
    voos = carregar_voos()
    return render_template("pag.html", voos=voos)

# --- Adicionar novo voo ---
@app.route("/adicionar_voo", methods=["POST"])
def adicionar_voo():
    codigo = request.form.get("codigo")
    origem = request.form.get("origem")
    destino = request.form.get("destino")
    preco = float(request.form.get("preco"))

    voos = carregar_voos()
    voos.append({
        "codigo": codigo,
        "origem": origem,
        "destino": destino,
        "preco": preco
    })

    salvar_voos(voos)
    return redirect(url_for("painel_admin"))

# --- Remover voo pelo código ---
@app.route("/remover_voo", methods=["POST"])
def remover_voo():
    codigo = request.form.get("codigo")

    voos = carregar_voos()
    voos = [v for v in voos if v["codigo"] != codigo]

    salvar_voos(voos)
    return redirect(url_for("painel_admin"))

# --- Função auxiliar para salvar os voos ---
def salvar_voos(voos):
    try:
        with open("listaVoos.text", "w", encoding="utf-8") as f:
            f.write("Voos = " + str(voos))
    except Exception as e:
        print(f"Erro ao salvar voos: {e}")

# --- Executa o app ---
if __name__ == "__main__":
    app.run(debug=True)

# colocar uma barra de navegação para "descer" os voos cadastrados
# colocar os voos já na lista na tabela da primeira pagina
# edições de voo (adicionar e excluir) apenas para administradores!