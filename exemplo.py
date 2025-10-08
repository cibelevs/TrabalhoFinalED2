from flask import Flask, render_template, request, redirect # <-- Mudar aqui!

app = Flask(__name__)

#função para carregar o arquivo
def carrega_voos():
    try:
        with open("arquivos/listaVoos.text", "r", encoding="utf-8") as f:
            conteudo = f.read()
            exec(conteudo, globals())  # Cria a lista Voos
            return globals().get("Voos", [])
    except Exception as e:
        print("Erro ao carregar voos:", e)
        return []

def adiciona_voos(novo_voo):
    try:
        with open("arquivos/listaVoos.text", "a", encoding="utf-8") as f:
            f.write(f"\nVoos.append({novo_voo})")
    except Exception as e:
        print("Erro ao adicionar voo:", e)

def retira_voo(codigo):
    voos = carrega_voos()
    voos = [v for v in voos if v["codigo"] != codigo]
    try:
        with open("/home/cibele/Documentos/TrabalhoFinalED2/arquivos/listaVoos.text", "w", encoding="utf-8") as f:
            f.write(f"Voos = {voos}")
    except Exception as e:
        print("Erro ao remover voo:", e)

#Pagina inicial 
@app.route('/')
def home():
        return render_template('menu.html')


@app.route('/usuario')
def tela_usuario():
    # Certifique-se de que o template 'usuario.html' existe na pasta 'templates'
    return render_template('usuario.html')

# add no main um metodo
@app.route('/remover_voo/<codigo>', methods=['POST'])
def remover_voo(codigo):
    retira_voo(codigo)
    return redirect('/voos')


# --- Processa o login e redireciona ---
@app.route('/login', methods=['POST'])
def login():
    """Processa o formulário de login."""
    try:
        nome = request.form['nome'] 
        senha = request.form['senha']
    except KeyError:
        # Se os campos do formulário não forem encontrados
        return "<h3>Erro: Campos de login ausentes. Verifique o seu 'usuario.html'.</h3>"


    # Simulação de verificação de usuário/senha
    if nome == "admin" and senha == "123":
        return redirect('/voos') 
    else:
        return "<h3>Usuário ou senha incorretos! <a href='/'>Tente novamente</a></h3>"

# --- Listagem de voos ---
@app.route('/voos')
def listar_voos():
    voos = carrega_voos()
    print("Lista de voos carregada do arquivo:\n")
    for v in voos:
        print(f"Código: {v['codigo']}, Origem: {v['origem']}, Destino: {v['destino']}, Preço: R$ {v['preco']:.2f}")
    return render_template('voos.html', voos=voos)
if __name__ == "__main__":
    app.run(debug=True)

# colocar uma barra de navegação para "descer" os voos cadastrados
# colocar os voos já na lista na tabela da primeira pagina
# edições de voo (adicionar e excluir) apenas para administradores!