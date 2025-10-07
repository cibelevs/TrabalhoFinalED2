from flask import Flask, render_template, request, redirect # <-- Mudar aqui!

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



# --- Rota Principal: Tela inicial (login do usuário) ---
# Esta rota agora é a única definida para '/', exibindo o login.
@app.route('/')
def tela_usuario():
    # Certifique-se de que o template 'usuario.html' existe na pasta 'templates'
    return render_template('usuario.html')


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

