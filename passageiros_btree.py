import pandas as pd
from BTreeBiblioteca import BTree

class Passageiro:
    def __init__(self, cpf, voo, origem, destino, horario):
        self.cpf = str(cpf)
        self.voo = str(voo)
        self.origem = origem
        self.destino = destino
        self.horario = horario

    def __repr__(self):
        return f"Passageiro(cpf={self.cpf}, voo={self.voo})"


class PassageirosBTree:
    def __init__(self, ordem=3):
        self.btree = BTree(ordem)
        self.passageiros_por_voo = {}

    # ------------------------------------
    # CARREGA CSV E INSERE NA ÁRVORE-B
    # ------------------------------------
    def carregar_csv(self, caminho_csv):
        try:
            df = pd.read_csv(
                caminho_csv,
                header=None,
                names=["cpf", "voo", "origem", "destino", "horario"]
            )
        except FileNotFoundError:
            return

        for _, row in df.iterrows():
            self.inserir_passageiro(
                cpf=row["cpf"],
                voo=row["voo"],
                origem=row["origem"],
                destino=row["destino"],
                horario=row["horario"]
            )

    # ------------------------------------
    # INSERIR PASSAGEIRO NA ÁRVORE-B
    # ------------------------------------
    def inserir_passageiro(self, cpf, voo, origem, destino, horario):
        passageiro = Passageiro(cpf, voo, origem, destino, horario)

        # inserir por CPF
        self.btree.inserir(str(cpf), passageiro)

        # Agrupar por voo
        if voo not in self.passageiros_por_voo:
            self.passageiros_por_voo[voo] = []

        self.passageiros_por_voo[voo].append(passageiro)

    # ------------------------------------
    # BUSCAR POR CPF
    # ------------------------------------
    def buscar_por_cpf(self, cpf):
        return self.btree.buscar(str(cpf))

    # ------------------------------------
    # LISTAR (ORDENADO) POR CPF
    # ------------------------------------
    def listar_ordenado(self):
        return self.btree.listar_chave_valor()

    # ------------------------------------
    # LISTAR POR CÓDIGO DO VOO
    # ------------------------------------
    def listar_por_voo(self, codigo_voo):
        return self.passageiros_por_voo.get(codigo_voo, [])
