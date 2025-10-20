import os
import ast
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages


app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # pode ser qualquer string


# --- Função para carregar voos do arquivo dentro da pasta 'arquivos' ---
def carregar_voos():
    try:
        caminho = os.path.join("arquivos", "listaVoos.text")
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if conteudo.startswith("Voos ="):
                conteudo = conteudo.split("=", 1)[1].strip()
            voos = ast.literal_eval(conteudo)
            return voos if isinstance(voos, list) else []
    except Exception as e:
        print(f"Erro ao carregar voos: {e}")
        return []

# --- Função auxiliar para salvar os voos ---
def salvar_voos(voos):
    try:
        caminho = os.path.join("arquivos", "listaVoos.text")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("Voos = " + str(voos))
    except Exception as e:
        print(f"Erro ao salvar voos: {e}")

# --- Página inicial (menu principal) ---
@app.route('/')
def home():
    voos = carregar_voos()
    return render_template('menu.html', voos=voos)

def carregar_usuarios():
    try:
        caminho = os.path.join("arquivos", "usuarios.text")
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()
            if conteudo.startswith("Usuarios ="):
                conteudo = conteudo.split("=", 1)[1].strip()
            usuarios = ast.literal_eval(conteudo)
            return usuarios if isinstance(usuarios, list) else []
    except Exception as e:
        print(f"Erro ao carregar usuários: {e}")
        return []

def salvar_usuarios(usuarios):
    try:
        caminho = os.path.join("arquivos", "usuarios.text")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("Usuarios = " + str(usuarios))
    except Exception as e:
        print(f"Erro ao salvar usuários: {e}")


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    usuarios = carregar_usuarios()

    if any(u['nome'] == nome for u in usuarios):
        return render_template('cadastro.html', erro="Nome de usuário já existe!")

    usuarios.append({"nome": nome, "senha": senha})
    salvar_usuarios(usuarios)
    return render_template('acesso_adm.html', sucesso="Conta criada com sucesso! Faça login.")

@app.route('/login_usuario')
def login_usuario():
    return render_template('login_usuario.html')

@app.route('/login_usuario', methods=['POST'])
def login_usuario_post():
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    usuarios = carregar_usuarios()  # função que lê usuarios.text

    # procura usuário com nome e senha corretos
    usuario_valido = any(u.get('nome') == nome and u.get('senha') == senha for u in usuarios)
    if usuario_valido:
        return redirect(url_for('painel_usuario'))

    # login inválido
    return """
    <h3 style='color:red; text-align:center;'>Usuário ou senha incorretos!</h3>
    <div style='text-align:center;'><a href='/login_usuario' style='color:#ff7b00;'>Voltar</a></div>
    """


# --- Página de login ---
@app.route('/administrador')
def tela_usuario():
    return render_template('acesso_adm.html')

# --- Login simples para administrador ---
@app.route('/login', methods=['POST'])
def login():
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    if nome == 'admin' and senha == '123':
        return redirect(url_for('painel_admin'))
    

    usuarios = carregar_usuarios()
    if any(u['nome'] == nome and u['senha'] == senha for u in usuarios):
        return redirect(url_for('painel_usuario'))
    else:
        return """
        <h3 style='color:red; text-align:center;'>Usuário ou senha incorretos!</h3>
        <div style='text-align:center;'><a href='/' style='color:#ff7b00;'>Voltar</a></div>
        """

# --- Painel do administrador ---
@app.route('/painel_admin')
def painel_admin():
    voos = carregar_voos()
    return render_template('pag_adm.html', voos=voos)

@app.route('/painel_usuario')
def painel_usuario():
    voos = carregar_voos()
    return render_template('painelusuario.html', voos=voos)



# --- Página de consulta de voos pelo usuario ---
@app.route('/consultar_voos_usuario')
def consultar_voos_usuario():
    origem_busca = request.args.get('origem', '').lower()
    destino_busca = request.args.get('destino', '').lower()

    voos = carregar_voos()

    if origem_busca or destino_busca:
        voos = [
            v for v in voos
            if origem_busca in v['origem'].lower() and destino_busca in v['destino'].lower()
        ]

    # Essa página NÃO mostrará botões de edição e remoção
    return render_template('voos_usuario.html', voos=voos, origem=origem_busca, destino=destino_busca)

# --- Página de consulta de voos pelo adm ---
@app.route('/voos')
def voos_usuario():
    # Pega parâmetros de busca
    origem_busca = request.args.get('origem', '').lower()
    destino_busca = request.args.get('destino', '').lower()

    voos = carregar_voos()

    # Filtra voos se houver pesquisa
    if origem_busca or destino_busca:
        voos = [
            v for v in voos
            if origem_busca in v['origem'].lower() and destino_busca in v['destino'].lower()
        ]

    return render_template('voos.html', voos=voos, origem=origem_busca, destino=destino_busca)

# --- Adicionar voo ---
@app.route('/adicionar_voo', methods=['POST'])
def adicionar_voo():
    codigo = request.form.get('codigo')
    origem = request.form.get('origem')
    destino = request.form.get('destino')
    preco_str = request.form.get('preco')

    try:
        preco = float(preco_str)
    except (TypeError, ValueError):
        return render_template('pag_adm.html', error="Preço inválido.")

    voos = carregar_voos()

    # Verifica se código já existe
    if any(voo["codigo"] == codigo for voo in voos):
        return render_template('pag_adm.html', error=f"O código '{codigo}' já está em uso.", voos=voos)

    voos.append({"codigo": codigo, "origem": origem, "destino": destino, "preco": preco})
    salvar_voos(voos)
    return render_template('pag_adm.html', success="Voo adicionado com sucesso!", voos=voos)
# --- Remover Voo ---
@app.route('/remover_voo', methods=['POST'])
def remover_voo():
    origem = request.form.get('origem', '').strip().lower()
    destino = request.form.get('destino', '').strip().lower()

    voos = carregar_voos()
    voos_antes = len(voos)

    # Remove voo por origem e destino (ignorando maiúsculas/minúsculas)
    voos = [v for v in voos if not (
        v["origem"].strip().lower() == origem and 
        v["destino"].strip().lower() == destino
    )]

    salvar_voos(voos)
    
    if len(voos) < voos_antes:
        flash("Voo removido com sucesso!", "sucesso")
    else:
        flash("Nenhum voo encontrado com essa origem e destino.", "erro")

    return redirect(url_for('painel_admin'))


@app.route('/salvar_edicao', methods=['POST'])
def salvar_edicao():
    codigo = request.form.get('codigo')
    origem = request.form.get('origem')
    destino = request.form.get('destino')
    preco_str = request.form.get('preco')

    try:
        preco = float(preco_str)
    except (TypeError, ValueError):
        voos = carregar_voos()
        return render_template('pag_adm.html', error="Preço inválido.", voos=voos)

    voos = carregar_voos()
    for voo in voos:
        if voo["codigo"] == codigo:
            voo["origem"] = origem
            voo["destino"] = destino
            voo["preco"] = preco
            break

    salvar_voos(voos)
    return redirect(url_for('painel_admin'))


# --- Executa o app ---
if __name__ == '__main__':
    app.run(debug=True)

# O que falta adicionar/modificar: 
# Página para usuário (criar conta com login e senha)
# ---> colocar uma mens agem na página inicial (tem interesse de criar uma conta?)
# ---> fazer em dicionários 
# Aumentar a tabela de voos para ficarem mais visíveis.
# Fazer para que o usuário busque um dado de um voo (pela localidade)
# Tentar colocar alguma descrição dentro da página do administrador em que:
# ----->"voos internacionais começam com IN , voos no brasil começam com ED"
