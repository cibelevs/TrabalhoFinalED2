# --- CLASSE AUXILIAR VOO ---
# Em Python, criamos classes para agrupar dados e comportamentos.
# O método __init__ é o construtor, chamado quando um novo objeto é criado.
# O método __repr__ (ou __str__) define como o objeto será exibido ao ser impresso.
class Voo:
    def __init__(self, origem, destino, preco, assentos_total):
        self.origem = origem
        self.destino = destino
        self.preco = preco
        self.assentos_total = assentos_total

    def __repr__(self):
        return f"{{Origem={self.origem}, Destino={self.destino}, Preço={self.preco}}}\n"

# --- FUNÇÃO PRINCIPAL (EQUIVALENTE AO public static void main) ---
def main():
    # --- 1. DECLARAÇÃO E CRIAÇÃO DO DICIONÁRIO ---
    # Em Python, dicionários são criados com chaves {} ou com a função dict().
    # Não é necessário declarar os tipos de dados da chave e do valor.
    voos = {}

    # --- 2. ADICIONANDO DADOS ---
    # A sintaxe para adicionar ou atualizar um item é nome_do_dicionario[chave] = valor.
    voos["LA3412"] = Voo("São Paulo (GRU)", "Salvador (SSA)", 450.70, 180)
    voos["AD2870"] = Voo("Rio de Janeiro (GIG)", "Fortaleza (FOR)", 890.00, 118)
    voos["G31610"] = Voo("Belo Horizonte (CNF)", "Porto Alegre (POA)", 625.50, 186)

    print("--- Voos cadastrados ---")
    print(voos)
    print("\n")

# --- 3. ACESSANDO DADOS ---
# Padrão em Python para garantir que o código dentro do `if` só rode
# quando o script é executado diretamente.
if __name__ == "__main__":
    main()
