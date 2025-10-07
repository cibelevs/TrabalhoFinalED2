from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Olá, Flask está funcionando!'

def listarVoos():
    return 'voos serão listados aqui'
if __name__ == '__main__':
    app.run(debug=True)




