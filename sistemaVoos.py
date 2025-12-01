import os
import csv
import re
import ast
from flask import Flask, json, render_template, request, redirect, session, url_for, flash, get_flashed_messages
from passageiros_btree import PassageirosBTree 
import pandas as pd


app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  

# Inicialização da árvore B para passageiros
passageiros_db = PassageirosBTree(ordem=3)
passageiros_db.carregar_csv("arquivos/passageiros.csv")

# FUNÇÕES DE PERSISTÊNCIA DE DADOS
# -----------------------

# --- Funções para manipulação de voos ---
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


def salvar_voos(voos):
    try:
        caminho = os.path.join("arquivos", "listaVoos.text")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("Voos = " + str(voos))
    except Exception as e:
        print(f"Erro ao salvar voos: {e}")


# --- Funções para manipulação de usuários ---
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


# --- Funções para voos confirmados ---
def carregar_voos_confirmados():
    if not os.path.exists("arquivos/voos_confirmados.json"):
        return []

    with open("arquivos/voos_confirmados.json", "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []


def salvar_voos_confirmados(lista):
    with open("arquivos/voos_confirmados.json", "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=4)


# --- Funções para passageiros ---
def carregar_passageiros():
    df = pd.read_csv("arquivos/passageiros.csv")
    df = df.fillna("")  # evita NaN -> Undefined no template
    return df.to_dict(orient="records")


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


# ROTAS DE AUTENTICAÇÃO E CADASTRO
# -----------------------

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
    usuario_valido = next((u for u in usuarios if u.get('nome') == nome and u.get('senha') == senha), None)
    if usuario_valido:
        session["usuario_logado"] = usuario_valido  # salva dict completo
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))   # Volta para o menu

# ROTAS DO PAINEL ADMINISTRATIVO
# -----------------------

@app.route('/painel_admin')
def painel_admin():
    voos = carregar_voos()
    return render_template('pag_adm.html', voos=voos)


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

# ROTAS DO PAINEL DO USUÁRIO
# -----------------------


@app.route("/painel_usuario")
def painel_usuario():
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login primeiro.", "erro")
        return redirect(url_for("login_usuario"))

    # garantir estruturas
    meus_voos = session.get("meus_voos", [])
    voos_pendentes = session.get("voos_pendentes", [])
    passageiros_sessao = session.get("passageiros_voo", {})

    # filtrar voos pertencentes ao usuário
    meus_voos_usuario = [
        v for v in meus_voos
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]

    pendentes_usuario = [
        v for v in voos_pendentes
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]

    return render_template(
        "painelusuario.html",
        meus_voos=meus_voos_usuario,
        voos_pendentes=pendentes_usuario,
        passageiros_sessao=passageiros_sessao,
        voos=None,
        usuario=usuario
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


@app.route("/remover_passageiro/<codigo>", methods=["POST"])
def remover_passageiro(codigo):
    cpf = request.form.get("cpf")

    if not cpf:
        flash("CPF inválido!", "danger")
        return redirect(url_for("adicionar_voos_usuario"))

    # garantir existir
    passageiros_voo = session.get("passageiros_voo", {})
    lista = passageiros_voo.get(codigo, [])

    # remover
    nova_lista = [p for p in lista if p.get("cpf") != cpf]

    passageiros_voo[codigo] = nova_lista
    session["passageiros_voo"] = passageiros_voo
    session.modified = True

    flash("Passageiro removido com sucesso!", "success")
    return redirect(url_for("adicionar_voos_usuario"))


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
        passageiros_sessao=passageiros_sessao, usuario = usuario
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

# GESTÃO DE PASSAGEIROS POR VOO
# -----------------------

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


@app.route("/confirmar_passageiros", methods=["POST"])
def confirmar_passageiros():
    usuario = session.get("usuario_logado")
    codigo = session.get("codigo_voo_selecionado")

    if not usuario or not codigo:
        flash("Erro: voo ou usuário não encontrados.", "danger")
        return redirect(url_for("painel_usuario"))

    cpf_responsavel = request.form.get("cpf_responsavel", "").replace(".", "").replace("-", "")

    if not cpf_responsavel or len(cpf_responsavel) != 11:
        flash("CPF do responsável inválido!", "danger")
        return redirect(url_for("adicionar_voos_usuario"))

    # garantir estrutura da sessão
    if "passageiros_voo" not in session:
        session["passageiros_voo"] = {}

    # pegar passageiros já existentes vindo do form
    cpf_existentes = request.form.getlist("cpf_passageiros_existentes[]")

    # manter somente os passageiros que ainda existem
    passageiros_atualizados = [
        p for p in session["passageiros_voo"].get(codigo, [])
        if p["cpf"] in cpf_existentes
    ]

   
    # remover o usuário logado da lista (não deve aparecer como passageiro)
    passageiros_atualizados = [
        p for p in passageiros_atualizados
        if p["nome"].strip().lower() != usuario.strip().lower()
    ]
    nome_responsavel = request.form.get("nome_responsavel")

    if not nome_responsavel:
        flash("O nome completo do responsável é obrigatório.", "danger")
        return redirect(url_for("adicionar_voos_usuario"))

    passageiros_atualizados = [
        p for p in passageiros_atualizados
        if p.get("tipo") != "responsavel"
    ]

    passageiros_atualizados.append({
        "nome": nome_responsavel,
        "cpf": cpf_responsavel,
        "tipo": "responsavel"
    })

    nomes = request.form.getlist("novo_nome[]")
    cpfs = request.form.getlist("novo_cpf[]")
    tipos = request.form.getlist("novo_tipo[]")

    for nome, cpf, tipo in zip(nomes, cpfs, tipos):
        cpf = cpf.replace(".", "").replace("-", "")

        if nome and cpf:
            passageiros_atualizados.append({
                "nome": nome,
                "cpf": cpf,
                "tipo": tipo
            })

    session["passageiros_voo"][codigo] = passageiros_atualizados
    session.modified = True

    flash("Passageiros atualizados com sucesso!", "success")
    return redirect(url_for("adicionar_voos_usuario"))

# CONFIRMAÇÃO DE VOOS E REGISTRO DE PASSAGEIROS
# -----------------------


@app.route("/confirmar_voo/<codigo>", methods=["POST"])
def confirmar_voo(codigo):
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login para continuar.", "erro")
        return redirect(url_for("login_usuario"))

    #  Pegar passageiros registrados na sessão (lista daquele voo)
    passageiros_registrados = session.get("passageiros_voo", {}).get(codigo, [])

    # CPF do responsável
    cpf_usuario = request.form.get("cpf_usuario", "").strip()
    cpf_usuario = re.sub(r"\D", "", cpf_usuario)

    # fallback: se não vier no form
    if not cpf_usuario and isinstance(usuario, dict):
        cpf_usuario = re.sub(r"\D", "", str(usuario.get("cpf", "")))

    if not cpf_usuario or len(cpf_usuario) != 11:
        flash("CPF inválido!", "erro")
        return redirect(url_for("painel_usuario"))

    # Carregar voos
    todos_voos = carregar_voos()
    voo = next((v for v in todos_voos if v["codigo"] == codigo), None)

    if not voo:
        flash("Voo não encontrado!", "erro")
        return redirect(url_for("painel_usuario"))

    # Registrar passageiros
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

    # passageiros adicionais
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

    # 1. quantidade de passageiros
    qtd_passageiros = len(passageiros_registrados)

    # 2. atualizar assentos disponíveis
    voo["assentos_disponiveis"] -= qtd_passageiros

    # 3. salvar lista completa no arquivo
    def salvar_voos(todos_voos):
        with open("arquivos/listaVoos.txt", "w", encoding="utf-8") as f:
            for v in todos_voos:
                linha = (
                    f"{v['codigo']};{v['origem']};{v['destino']};"
                    f"{v['data']};{v['horario']};{v['preco']};"
                    f"{v['assentos_totais']};{v['assentos_disponiveis']}\n"
                )
                f.write(linha)

    # 4. atualizar arquivo
    salvar_voos(todos_voos)

    # remover voo da lista do usuário
    meus_voos = session.get("meus_voos", [])
    meus_voos = [v for v in meus_voos if v["codigo"] != codigo]
    session["meus_voos"] = meus_voos

    # ----------- CRIA O OBJETO DE CONFIRMAÇÃO -----------
    voo_confirmado = voo.copy()
    voo_confirmado["usuario"] = usuario
    voo_confirmado["confirmado"] = True

    # ----------- SALVAR EM ARQUIVO PERMANENTE -----------
    voos_arquivo = carregar_voos_confirmados()
    voos_arquivo.append(voo_confirmado)
    salvar_voos_confirmados(voos_arquivo)

    # ----------- SALVAR NA SESSÃO (opcional) -----------
    voos_pendentes = session.get("voos_pendentes", [])
    voos_pendentes.append(voo_confirmado)
    session["voos_pendentes"] = voos_pendentes

    # limpar passageiros da sessão
    if "passageiros_voo" in session:
        session["passageiros_voo"].pop(codigo, None)

    session.modified = True
    flash("Voo confirmado e passageiros registrados!", "sucesso")

    return redirect(url_for("painel_usuario"))

# VOOS CONFIRMADOS E CANCELAMENTOS
# -----------------------


@app.route("/voos_confirmados")
@app.route("/voos_confirmados")
def voos_confirmados():

    usuario = session.get("usuario_logado")
    if not usuario:
        return redirect(url_for("login_usuario"))

    voos_arquivo = carregar_voos_confirmados()
    voos_usuario = []

    for v in voos_arquivo:

        # Pega só os voos desse usuário
        if isinstance(v.get("usuario"), dict) and v["usuario"].get("nome") == usuario.get("nome"):

            preco = float(v.get("preco", 0))

            # Criar lista de passageiros corretamente
            if isinstance(v.get("usuario"), dict):
                passageiros = [v["usuario"]["nome"]]
            else:
                passageiros = []

            v["passageiros_lista"] = passageiros
            v["total_viagem"] = preco * len(passageiros)

            voos_usuario.append(v)

    return render_template("voos_confirmados.html", voos=voos_usuario)


@app.route("/remover_voo_confirmado/<codigo>", methods=["POST"])
def remover_voo_confirmado(codigo):

    usuario = session.get("usuario_logado")
    if not usuario:
        return redirect(url_for("login_usuario"))

    # Carregar voos
    voos = carregar_voos_confirmados()

    # Criar nova lista sem o voo cancelado
    voos_restante = []
    for v in voos:
        if (
            isinstance(v.get("usuario"), dict)
            and v["usuario"].get("nome") == usuario.get("nome")
            and str(v.get("codigo")) == str(codigo)
        ):
            continue  # este será removido
        voos_restante.append(v)

    salvar_voos_confirmados(voos_restante)

    flash("Voo cancelado com sucesso. Taxa de R$ 50,00 aplicada.", "warning")
    return redirect(url_for("voos_confirmados"))

# CONSULTA PÚBLICA DE VOOS (PÁGINA INICIAL)
# -----------------------

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


# ROTAS PARA ARVORE B (PASSAGEIROS) - PAINEL DO ADM
# -----------------------


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


# EXECUÇÃO DO APLICATIVO
# -----------------------

if __name__ == '__main__':
    app.run(debug=True)