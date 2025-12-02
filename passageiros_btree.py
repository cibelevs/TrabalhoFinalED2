import pandas as pd
from BTreeBiblioteca import BTree

class Passageiro:
    def __init__(self, nome, cpf, voo, origem, destino, horario):
        self.nome = nome
        self.cpf = cpf
        self.voo = voo
        self.origem = origem
        self.destino = destino
        self.horario = horario

    def __repr__(self):
        return f"Passageiro(nome={self.nome}, cpf={self.cpf}, voo={self.voo})"


class PassageirosBTree:
    def __init__(self, ordem=3):
        self.btree = BTree(ordem)
        self.passageiros_por_voo = {}

    # Somente cria o passageiro (não insere ainda)
    def criar_passageiro(self, nome, cpf, voo, origem, destino, horario):
        return Passageiro(nome, cpf, voo, origem, destino, horario)

    # Insere NA ÁRVORE e no agrupamento por voo
    def inserir(self, chave, passageiro):
        # Inserção na B-Tree
        self.btree.inserir(str(chave), passageiro)

        # Agrupar por voo
        if passageiro.voo not in self.passageiros_por_voo:
            self.passageiros_por_voo[passageiro.voo] = []

        self.passageiros_por_voo[passageiro.voo].append(passageiro)

    # Busca por CPF ou NOME
    def buscar(self, chave):
        return self.btree.buscar(str(chave))

    # Listagem ordenada de todos os passageiros
    def listar(self):
        """Retorna todos os passageiros em ordem pela chave da BTree."""
        lista = []

        def inorder(no):
            if no.folha:
                for v in no.valores:
                    lista.append(v)
                return

            for i in range(len(no.chaves)):
                inorder(no.filhos[i])
                lista.append(no.valores[i])
            inorder(no.filhos[-1])

        inorder(self.btree.raiz)
        return lista

    # Listagem por código do voo
    def listar_por_voo(self, codigo_voo):
        return self.passageiros_por_voo.get(codigo_voo, [])
