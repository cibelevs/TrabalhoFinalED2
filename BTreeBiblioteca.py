class NoB:
    def __init__(self, ordem):
        self.ordem = ordem
        self.chaves = []
        self.filhos = []
        self.valores = []
        self.folha = True

    def inserir_em_no(self, chave, valor):
        # Insere em um nó folha
        if not self.chaves:
            self.chaves.append(chave)
            self.valores.append(valor)
            return

        for i, item in enumerate(self.chaves):
            if chave < item:
                self.chaves.insert(i, chave)
                self.valores.insert(i, valor)
                return

        self.chaves.append(chave)
        self.valores.append(valor)


class BTree:
    def __init__(self, ordem):
        self.raiz = NoB(ordem)
        self.ordem = ordem

    # ------------------------ BUSCA ------------------------
    def buscar(self, chave, no=None):
        if no is None:
            no = self.raiz

        for i, item in enumerate(no.chaves):
            if chave == item:
                return no.valores[i]
            elif chave < item and not no.folha:
                return self.buscar(chave, no.filhos[i])

        if not no.folha:
            return self.buscar(chave, no.filhos[-1])

        return None

    # ------------------------ INSERÇÃO ------------------------
    def inserir(self, chave, valor):
        raiz = self.raiz

        if len(raiz.chaves) == self.ordem - 1:
            nova_raiz = NoB(self.ordem)
            nova_raiz.folha = False
            nova_raiz.filhos.append(self.raiz)
            self._dividir_no(nova_raiz, 0)
            self.raiz = nova_raiz

        self._inserir_nao_cheio(self.raiz, chave, valor)

    def _inserir_nao_cheio(self, no, chave, valor):
        if no.folha:
            no.inserir_em_no(chave, valor)
            return

        i = len(no.chaves) - 1
        while i >= 0 and chave < no.chaves[i]:
            i -= 1
        i += 1

        if len(no.filhos[i].chaves) == self.ordem - 1:
            self._dividir_no(no, i)
            if chave > no.chaves[i]:
                i += 1

        self._inserir_nao_cheio(no.filhos[i], chave, valor)

    def _dividir_no(self, pai, index):
        ordem = self.ordem
        no_cheio = pai.filhos[index]

        novo_no = NoB(ordem)
        novo_no.folha = no_cheio.folha

        meio = ordem // 2
        chave_meio = no_cheio.chaves[meio]
        valor_meio = no_cheio.valores[meio]

        pai.chaves.insert(index, chave_meio)
        pai.valores.insert(index, valor_meio)
        pai.filhos.insert(index + 1, novo_no)

        novo_no.chaves = no_cheio.chaves[meio + 1:]
        novo_no.valores = no_cheio.valores[meio + 1:]

        no_cheio.chaves = no_cheio.chaves[:meio]
        no_cheio.valores = no_cheio.valores[:meio]

        if not no_cheio.folha:
            novo_no.filhos = no_cheio.filhos[meio + 1:]
            no_cheio.filhos = no_cheio.filhos[:meio + 1]

    # ------------------------ LISTAGEM ------------------------
    def listar_chave_valor(self):
        lista = []
        self._inorder(self.raiz, lista)
        return lista

    def _inorder(self, no, lista):
        if no.folha:
            for c, v in zip(no.chaves, no.valores):
                lista.append((c, v))
            return

        for i in range(len(no.chaves)):
            self._inorder(no.filhos[i], lista)
            lista.append((no.chaves[i], no.valores[i]))

        self._inorder(no.filhos[-1], lista)
