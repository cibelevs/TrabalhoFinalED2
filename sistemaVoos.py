import os
import csv
import re
import ast
from flask import Flask, json, render_template, request, redirect, session, url_for, flash, get_flashed_messages
from passageiros_btree import PassageirosBTree 
import pandas as pd

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # pode ser qualquer string

passageiros_db = PassageirosBTree(ordem=3)
passageiros_db.carregar_csv("arquivos/passageiros.csv")

# --- Função para carregar voos do arquivo dentro da pasta 'arquivos' ---
def carregar_voos():
    try:
        caminho = os.path.join("arquivos", "listaVoos.text")

        if not os.path.exists(caminho):
            return []

        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read().strip()

            if conteudo.startswith("Voos ="):
                conteudo = conteudo.split("=", 1)[1].strip()

            voos = ast.literal_eval(conteudo)

            # 🔥 Normalizar chaves antigas
            for v in voos:

                # Caso tenha "assentos" → vira assentos_totais
                if "assentos" in v:
                    v["assentos_totais"] = v.pop("assentos")

                # Se existir assentos_disponiveis, senão iguala ao total
                if "assentos_disponiveis" not in v:
                    v["assentos_disponiveis"] = v.get("assentos_totais", 0)

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
    return render_template('login_usuario.html', sucesso="Conta criada com sucesso! Faça login.")

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
        session["usuario_logado"] = usuario_valido
        session.modified = True
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


def carregar_passageiros():
    df = pd.read_csv("arquivos/passageiros.csv")
    df = df.fillna("")  # evita NaN -> Undefined no template
    return df.to_dict(orient="records")

@app.route("/painel_usuario")
def painel_usuario():
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login primeiro.", "erro")
        return redirect(url_for("login_usuario"))

    # garantir estruturas na sessão
    meus_voos = session.get("meus_voos", [])
    voos_pendentes = session.get("voos_pendentes", [])
    # passageiros salvos por código na session (estrutura esperada: {codigo: [ {nome,cpf,tipo}, ... ]})
    passageiros_sessao = session.get("passageiros_voo", {})

    # filtrar só os do usuário
    meus_voos_usuario = [
        v for v in meus_voos
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]
    pendentes_usuario = [
        v for v in voos_pendentes
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]

    meus_voos = [
        v for v in session.get("meus_voos", [])
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]


    voos_pendentes = [
        v for v in session.get("voos_pendentes", [])
        if v.get("usuario") == usuario
    ]

    return render_template(
        "painelusuario.html",
        meus_voos=meus_voos_usuario,
        voos_pendentes=pendentes_usuario,
        passageiros_sessao=passageiros_sessao,
        voos=None, 
        usuario = usuario
    )




# --- Página de consulta de voos pelo usuario ---
def carregar_meus_voos():
    if "meus_voos" not in session:
        session["meus_voos"] = []
    return session["meus_voos"]



@app.route("/adicionar_voos_usuario")
def adicionar_voos_usuario():
    usuario = session.get("usuario_logado")
    if not usuario:
        return redirect(url_for("login_usuario"))

    codigo = session.get("codigo_voo_selecionado")

    # CARREGAR VOOS DO ARQUIVO
    todos = carregar_voos()
    voo = next((v for v in todos if v["codigo"] == codigo), None)

    # GARANTIR E BUSCAR PASSAGEIROS DO VOO
    passageiros_existentes = []
    if "passageiros_voo" in session and codigo in session["passageiros_voo"]:
        passageiros_existentes = session["passageiros_voo"][codigo]

    return render_template(
        "adicionar_voos_usuario.html",
        voo=voo,
        passageiros_existentes=passageiros_existentes,
        codigo=codigo
    )



def adicionar_voo_usuario(codigo_voo):
    usuario = session.get("usuario_logado")
    if not usuario:
        return False

    # Carrega lista de voos disponíveis
    todos = carregar_voos()
    voo = next((v for v in todos if v["codigo"] == codigo_voo), None)

    if not voo:
        return False

    # Garantir lista da sessão
    meus_voos = session.get("meus_voos", [])

    # Verifica se o voo já existe para esse usuário (sem KeyError)
    for v in meus_voos:
        if v.get("codigo") == voo["codigo"] and v.get("usuario") == usuario:
            return True  # já existe, não duplica

    # Criar voo NÃO confirmado
    novo_voo = {
        "codigo": voo["codigo"],
        "origem": voo["origem"],
        "destino": voo["destino"],
        "preco": voo["preco"],
        "usuario": usuario,
        "confirmado": False,
        "passageiros": []
    }

    meus_voos.append(novo_voo)

    session["meus_voos"] = meus_voos
    session.modified = True
    return True



def remover_voo_usuario(codigo_voo):
    meus_voos = carregar_meus_voos()
    meus_voos = [v for v in meus_voos if v["codigo"] != codigo_voo]
    session["meus_voos"] = meus_voos
    session.modified = True


@app.get("/buscar_voos_usuario")
def buscar_voos_usuario():
    usuario = session.get("usuario_logado")
    if not usuario:
        return redirect(url_for("login_usuario"))

    origem = request.args.get("origem", "").strip().lower()
    destino = request.args.get("destino", "").strip().lower()

    todos = carregar_voos()
    voos_filtrados = [
        v for v in todos
        if origem in v["origem"].lower() and destino in v["destino"].lower()
    ]

    # manter consistência com painel_usuario()
    meus_voos = [
        v for v in session.get("meus_voos", [])
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]
    pendentes = [
        v for v in session.get("voos_pendentes", [])
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]

    passageiros_sessao = carregar_passageiros()

    return render_template(
        "painelusuario.html",
        voos=voos_filtrados,
        meus_voos=meus_voos,
        voos_pendentes=pendentes,
        passageiros_sessao=passageiros_sessao
    )


@app.post("/adicionar_ao_carrinho/<codigo>")
def adicionar_ao_carrinho(codigo):
    adicionar_voo_usuario(codigo)
    flash("Voo adicionado aos seus voos!", "sucesso")

    
    return redirect(url_for("painel_usuario"))

@app.post("/remover_do_carrinho/<codigo>")
def remover_do_carrinho(codigo):
    remover_voo_usuario(codigo)
    flash("Voo removido dos seus voos.", "sucesso")
    return redirect(url_for("painel_usuario"))


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


@app.route('/voos')
def voos():
    return render_template('voos.html', voos=voos)


# --- Adicionar voo ---

@app.route('/adicionar_voo', methods=['POST'])
def adicionar_voo():
    codigo = request.form.get('codigo')
    origem = request.form.get('origem')
    destino = request.form.get('destino')
    preco_str = request.form.get('preco')
    data = request.form.get('data')
    horario = request.form.get('horario')
    assentos_totais_str = request.form.get('assentos_totais')

    try:
        preco = float(preco_str)
        assentos_totais = int(assentos_totais_str)
    except:
        flash("Preço ou assentos inválidos.", "erro")
        return redirect(url_for('painel_admin'))

    voos = carregar_voos()

    # Impedir duplicação
    if any(voo["codigo"] == codigo for voo in voos):
        flash(f"O código '{codigo}' já está em uso.", "erro")
        return redirect(url_for('painel_admin'))

    # Adicionar novo voo
    voos.append({
        "codigo": codigo,
        "origem": origem,
        "destino": destino,
        "preco": preco,
        "data": data,
        "horario": horario,
        "assentos_totais": assentos_totais,
        "assentos_disponiveis": assentos_totais
    })

    salvar_voos(voos)

    flash("Voo adicionado com sucesso!", "sucesso")
    return redirect(url_for('painel_admin'))


# usuario seleciona voo
@app.route("/selecionar_voo/<codigo>")
def selecionar_voo(codigo):
    session["codigo_voo_selecionado"] = codigo

    # Inicializa lista caso ainda não exista
    if "passageiros_voo" not in session:
        session["passageiros_voo"] = {}

    if codigo not in session["passageiros_voo"]:
        session["passageiros_voo"][codigo] = []

    return redirect(url_for("adicionar_voos_usuario"))

# usuario adiciona voos
def adicionar_voo_usuario(codigo_voo):
    usuario = session.get("usuario_logado")
    if not usuario:
        return False

    todos = carregar_voos()
    voo = next((v for v in todos if v["codigo"] == codigo_voo), None)

    if not voo:
        return False

    meus_voos = session.get("meus_voos", [])

    # Já adicionado?
    for v in meus_voos:
        if v.get("codigo") == voo["codigo"] and v.get("usuario") == usuario:
            return True

    novo_voo = {
        "codigo": voo["codigo"],
        "origem": voo["origem"],
        "destino": voo["destino"],
        "data": voo["data"],
        "horario": voo["horario"],
        "preco": voo["preco"],
        "assentos_totais": voo["assentos_totais"],
        "assentos_disponiveis": voo["assentos_disponiveis"],
        "usuario": usuario,
        "confirmado": False,
        "passageiros": []
    }

    meus_voos.append(novo_voo)
    session["meus_voos"] = meus_voos
    session.modified = True
    return True



@app.route("/voos_confirmados")
def voos_confirmados():

    usuario = session.get("usuario_logado")
    if not usuario:
        return redirect(url_for("login_usuario"))

    voos = [
        v for v in session.get("voos_pendentes", [])
        if v.get("usuario") == usuario
    ]

    return render_template("voos_confirmados.html", voos=voos)



# confirma passageiros do usuario
# confirma passageiros do usuario
@app.route("/confirmar_passageiros", methods=["POST"])
def confirmar_passageiros():
    usuario = session.get("usuario_logado")
    codigo = session.get("codigo_voo_selecionado")  # voo atual

    if not usuario or not codigo:
        flash("Erro: voo ou usuário não encontrados.", "danger")
        return redirect(url_for("painel_usuario"))

    # --------------------------
    # PEGAR CPF DO RESPONSÁVEL
    # --------------------------
    cpf_responsavel = request.form.get("cpf_responsavel", "").strip()
    cpf_responsavel = cpf_responsavel.replace(".", "").replace("-", "")

    if not cpf_responsavel or len(cpf_responsavel) != 11 or not cpf_responsavel.isdigit():
        flash("CPF do responsável inválido!", "danger")
        return redirect(url_for("adicionar_voos_usuario"))

    # Salvar cpf_responsavel dentro da sessão com chave por código
    if "passageiros_responsavel" not in session:
        session["passageiros_responsavel"] = {}

    session["passageiros_responsavel"][codigo] = cpf_responsavel
    # ----------------------------

    # Garante estrutura dos passageiros adicionais
    if "passageiros_voo" not in session:
        session["passageiros_voo"] = {}

    if codigo not in session["passageiros_voo"]:
        session["passageiros_voo"][codigo] = []

    passageiros_existentes = session["passageiros_voo"][codigo]

    # CAPTURAR PASSAGEIROS NOVOS
    nomes = request.form.getlist("novo_nome[]")
    cpfs = request.form.getlist("novo_cpf[]")
    tipos = request.form.getlist("novo_tipo[]")

    # ADICIONAR PASSAGEIROS NA LISTA DO CÓDIGO
    for nome, cpf, tipo in zip(nomes, cpfs, tipos):
        nome = nome.strip()
        cpf = cpf.strip().replace(".", "").replace("-", "")

        if nome and cpf:
            passageiros_existentes.append({
                "nome": nome,
                "cpf": cpf,
                "tipo": tipo
            })

    # SALVAR NA SESSION
    session["passageiros_voo"][codigo] = passageiros_existentes
    session.modified = True

    flash("Passageiros e CPF do responsável salvos!", "success")
    return redirect(url_for("adicionar_voos_usuario"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))   # Volta para o menu



@app.route("/confirmar_voo/<codigo>", methods=["POST"])
def confirmar_voo(codigo):
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login para continuar.", "erro")
        return redirect(url_for("login_usuario"))

    #  Pegar passageiros registrados na sessão (lista daquele voo)
    passageiros_registrados = session.get("passageiros_voo", {}).get(codigo, [])

    # CPF do responsável pelo voo (tente form, se vazio tente sessão)
    cpf_usuario = request.form.get("cpf_usuario", "").strip()

    # sanitizar: remover pontos, traços, espaços — deixar só dígitos
    cpf_usuario = re.sub(r"\D", "", cpf_usuario)

    # se veio vazio no form, tente obter do usuario salvo na sessão (caso você tenha salvo o dict do usuário)
    if not cpf_usuario:
        if isinstance(usuario, dict):
            cpf_usuario = usuario.get("cpf", "")
            # também sanitizar caso venha com formatação
            cpf_usuario = re.sub(r"\D", "", str(cpf_usuario))
        else:
            # fallback (não ideal) — tenta converter para string e extrair dígitos
            cpf_usuario = re.sub(r"\D", "", str(usuario))

    # validação final
    if not cpf_usuario or len(cpf_usuario) != 11 or not cpf_usuario.isdigit():
        flash("CPF inválido! Verifique se o CPF do responsável está preenchido corretamente.", "erro")
        return redirect(url_for("painel_usuario"))

    #  Carregar todos os voos cadastrados
    todos_voos = carregar_voos()

    voo = next((v for v in todos_voos if v["codigo"] == codigo), None)
    if not voo:
        flash("Voo não encontrado!", "erro")
        return redirect(url_for("painel_usuario"))

    

    # 4. Registrar passageiro responsável + outros passageiros
    registros_para_csv = []

    # passageiro principal
    passageiros_db.inserir_passageiro(
        cpf=cpf_usuario,
        voo=voo["codigo"],
        origem=voo["origem"],
        destino=voo["destino"],
        horario=voo["horario"]
    )

    registros_para_csv.append([cpf_usuario, voo["codigo"], voo["origem"], voo["destino"], voo["horario"]])

    # outros passageiros
    for p in passageiros_registrados:
        passageiros_db.inserir_passageiro(
            cpf=p["cpf"],
            voo=voo["codigo"],
            origem=voo["origem"],
            destino=voo["destino"],
            horario=voo["horario"]
        )
        registros_para_csv.append([p["cpf"], voo["codigo"], voo["origem"], voo["destino"], voo["horario"]])

    salvar_passageiros_csv(registros_para_csv)

    # 5. Remover da lista "meus_voos"
    meus_voos = session.get("meus_voos", [])
    meus_voos = [v for v in meus_voos if v["codigo"] != codigo]
    session["meus_voos"] = meus_voos

    # 6. Mover para voos pendentes
    voos_pendentes = session.get("voos_pendentes", [])
    voo_confirmado = voo.copy()
    voo_confirmado["usuario"] = usuario
    voo_confirmado["confirmado"] = True
    voos_pendentes.append(voo_confirmado)
    session["voos_pendentes"] = voos_pendentes

    # limpar passageiros da sessão
    if "passageiros_voo" in session:
        session["passageiros_voo"].pop(codigo, None)


  
    

    session.modified = True
    flash("Voo confirmado e passageiros registrados!", "sucesso")

    return redirect(url_for("painel_usuario"))



def salvar_passageiros_csv(linhas):
    caminho = os.path.join("arquivos", "passageiros.csv")

    arquivo_existe = os.path.exists(caminho)

    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # escrever cabeçalho se o arquivo está vazio
        if not arquivo_existe:
            writer.writerow(["cpf", "voo", "origem", "destino", "horario"])

        # grava cada passageiro confirmado
        for linha in linhas:
            writer.writerow(linha)


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

    return redirect(url_for('voos'))


@app.route('/salvar_edicao', methods=['POST'])
def salvar_edicao():
    codigo = request.form.get('codigo')
    origem = request.form.get('origem')
    destino = request.form.get('destino')
    preco_str = request.form.get('preco')
    data = request.form.get('data')
    horario = request.form.get('horario')
    assentos_totais_str = request.form.get('assentos_totais')

    try:
        preco = float(preco_str)
        assentos_totais = int(assentos_totais_str)
    except:
        voos = carregar_voos()
        return render_template('consulta_voos.html', error="Preço ou assentos inválidos.", voos=voos)

    voos = carregar_voos()

    voo_atual = None

    for voo in voos:
        if voo["codigo"] == codigo:
            voo["origem"] = origem
            voo["destino"] = destino
            voo["preco"] = preco
            voo["data"] = data
            voo["horario"] = horario

            diferenca = assentos_totais - voo.get("assentos_totais", 0)
            voo["assentos_totais"] = assentos_totais
            voo["assentos_disponiveis"] = max(0, voo.get("assentos_disponiveis", 0) + diferenca)

            voo_atual = voo
            break

    salvar_voos(voos)

    return render_template(
        'voos.html',
        voos=voos,
        abrir_modal=True,
        voo_atual=voo_atual
    )



@app.route("/", methods=["GET"])
def index():
    origem = request.args.get("origem", "").strip()
    destino = request.args.get("destino", "").strip()
    voos = []

    if origem or destino:
        todos_voos = carregar_voos()
        voos = [
            v for v in todos_voos
            if origem.lower() in v["origem"].lower() and destino.lower() in v["destino"].lower()
        ]

    return render_template("menu.html", origem=origem, destino=destino, voos=voos)

# --- Executa o app ---




# --- ---------------------  ARVORE B  ------------------------------ 
# ------------------------------------------------------------
# ------------------------------------------------------------
# PAINEL DO ADM — LISTAR PASSAGEIROS POR VOO

# --- ROTAS PARA BUSCA / LISTAGEM DE PASSAGEIROS (BTree) ---
@app.route('/buscar_passageiro_cpf')
def buscar_passageiro_cpf():
    cpf = request.args.get('cpf', '').strip()
    passageiro = passageiros_db.buscar_por_cpf(cpf)
    # use o template que você realmente criou (buscar_passageiro.html ou buscar_passageiro_manual.html)
    return render_template('buscar_passageiro.html', passageiro=passageiro, cpf=cpf)


@app.route('/listar_passageiros')
def listar_passageiros():
    lista = passageiros_db.listar_ordenado()  # retorna [(cpf, passageiro_obj), ...]
    return render_template('listar_passageiros.html', passageiros=lista)

if __name__ == '__main__':
    app.run(debug=True)