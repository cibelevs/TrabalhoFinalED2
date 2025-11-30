import os
import ast
from flask import Flask, json, render_template, request, redirect, session, url_for, flash, get_flashed_messages

app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"  # pode ser qualquer string


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
        session["usuario_logado"] = nome
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

@app.route("/painel_usuario")
def painel_usuario():
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login primeiro.", "erro")
        return redirect(url_for("login_usuario"))

    # garantir estruturas na sessão
    meus_voos = session.get("meus_voos", [])
    voos_pendentes = session.get("voos_pendentes", [])

    # passageiros salvos por código na session
    passageiros_sessao = session.get("passageiros_voo", {})

    # filtrar só os do usuário
    meus_voos_usuario = [
        v for v in meus_voos
        if v.get("usuario") == usuario and not v.get("confirmado", False)
    ]
    pendentes_usuario = [
        v for v in voos_pendentes
        if v.get("usuario") == usuario
    ]

    return render_template(
        "painelusuario.html",
        meus_voos=meus_voos_usuario,
        voos_pendentes=pendentes_usuario,
        passageiros_sessao=passageiros_sessao
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


@app.route("/buscar_voos_usuario")
def buscar_voos_usuario():
    origem = request.args.get("origem", "").strip().lower()
    destino = request.args.get("destino", "").strip().lower()
    todos = carregar_voos()
    voos = [
        v for v in todos
        if origem in v["origem"].lower() and destino in v["destino"].lower()
    ]
    return render_template("painelusuario.html", voos=voos, meus_voos=carregar_meus_voos())


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
@app.route("/confirmar_passageiros", methods=["POST"])
def confirmar_passageiros():
    usuario = session.get("usuario_logado")
    codigo = session.get("codigo_voo_selecionado")

    if not usuario or not codigo:
        flash("Erro: voo ou usuário não encontrados.", "danger")
        return redirect(url_for("painel_usuario"))

    # Garante estrutura
    if "passageiros_voo" not in session:
        session["passageiros_voo"] = {}

    if codigo not in session["passageiros_voo"]:
        session["passageiros_voo"][codigo] = []

    passageiros_existentes = session["passageiros_voo"][codigo]

    # CAPTURAR PASSAGEIROS NOVOS
    nomes = request.form.getlist("novo_nome[]")
    cpfs = request.form.getlist("novo_cpf[]")
    tipos = request.form.getlist("novo_tipo[]")

    # ADICIONAR NA LISTA
    for nome, cpf, tipo in zip(nomes, cpfs, tipos):
        if nome.strip() and cpf.strip():
            passageiros_existentes.append({
                "nome": nome,
                "cpf": cpf,
                "tipo": tipo
            })

    # SALVAR NOVAMENTE NA SESSION
    session["passageiros_voo"][codigo] = passageiros_existentes
    session.modified = True

    flash("Alterações salvas com sucesso!", "success")
    return redirect(url_for("adicionar_voos_usuario"))

@app.route("/remover_passageiro", methods=["POST"])
def remover_passageiro():
    codigo = session.get("codigo_voo_selecionado")
    idx = int(request.form.get("id", -1))

    if codigo not in session.get("passageiros_voo", {}):
        flash("Erro ao remover passageiro.", "danger")
        return redirect(url_for("adicionar_voos_usuario"))

    if 0 <= idx < len(session["passageiros_voo"][codigo]):
        session["passageiros_voo"][codigo].pop(idx)
        session.modified = True
        flash("Passageiro removido!", "success")

    return redirect(url_for("adicionar_voos_usuario"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))   # Volta para o menu



@app.route("/confirmar_voo/<codigo>", methods=["POST"])
def confirmar_voo(codigo):
    codigo = str(codigo)
    usuario = session.get("usuario_logado")
    if not usuario:
        flash("Faça login primeiro.", "erro")
        return redirect(url_for("login_usuario"))

    # Garantir listas
    meus_voos = session.get("meus_voos", [])
    voos_pendentes = session.get("voos_pendentes", [])

    # Procurar e remover o voo em meus_voos (apenas do usuário)
    voo_encontrado = None
    novos_meus_voos = []
    for v in meus_voos:
        if str(v.get("codigo")) == codigo and v.get("usuario") == usuario:
            voo_encontrado = v
            # não adiciona à lista nova = efetivamente remove
        else:
            novos_meus_voos.append(v)

    session["meus_voos"] = novos_meus_voos

    if not voo_encontrado:
        flash("Voo não encontrado entre seus voos não confirmados.", "danger")
        return redirect(url_for("painel_usuario"))

    # Atualizar o estado / certificações do objeto antes de mover
    voo_encontrado["confirmado"] = True
    voo_encontrado.setdefault("passageiros", voo_encontrado.get("passageiros", []))
    voo_encontrado["usuario"] = usuario  # garante consistência

    # Evitar duplicados em voos_pendentes (mesmo codigo + usuario)
    existe = any(
        vp.get("codigo") == voo_encontrado.get("codigo") and vp.get("usuario") == usuario
        for vp in voos_pendentes
    )
    if not existe:
        voos_pendentes.append(voo_encontrado)
        session["voos_pendentes"] = voos_pendentes

    session.modified = True
    flash("Voo disponível na aba Voos Pendentes! (confirmado)", "success")
    return redirect(url_for("painel_usuario"))



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
if __name__ == '__main__':
    app.run(debug=True)


