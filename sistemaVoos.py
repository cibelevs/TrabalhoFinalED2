import os
import ast
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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

# --- Página de login ---
@app.route('/administrador')
def tela_usuario():
    return render_template('acesso_adm.html')

# --- Login simples para administrador ---
@app.route('/loginAdm', methods=['POST'])
def login():
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    if nome == 'admin' and senha == '123':
        return redirect(url_for('painel_admin'))
    else:
        return """
        <h3 style='color:red; text-align:center;'>Usuário ou senha incorretos!</h3>
        <div style='text-align:center;'><a href='/' style='color:#ff7b00;'>Voltar</a></div>
        """

# --- Painel do administrador ---
@app.route('/painel')
def painel_admin():
    voos = carregar_voos()
    return render_template('pag_adm.html', voos=voos)

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

# --- Remover voo ---
@app.route('/remover_voo', methods=['POST'])
def remover_voo():
    codigo = request.form.get('codigo')
    voos = carregar_voos()
    voos = [v for v in voos if v["codigo"] != codigo]
    salvar_voos(voos)
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
# Não permitir os voos com os mesmos códigos! Na hora de deletar está excluindo os dois
# Adicionar algum tipo de diferencial nessa parte (horarios dos voos, cadeiras disponiveis?)
# Tentar colocar alguma descrição dentro da página do administrador em que:
# ----->"voos internacionais começam com IN , voos no brasil começam com ED"
