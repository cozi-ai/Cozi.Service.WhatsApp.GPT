from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import openai
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import os

openai.api_key = "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"

app = Flask(__name__)
absolute_path = os.path.dirname(os.path.abspath(__file__))
relative_path = "database/openai.db"
db_path = os.path.join(absolute_path, relative_path)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

def check_sessions():
    with app.app_context():
        limit = datetime.utcnow() - timedelta(minutes=60)
        Session.query.filter(Session.last_activity < limit).delete()
        print("Passei por aqui")
        db.session.commit()

class Session(db.Model):
    id = db.Column(db.String, primary_key=True)
    messages = db.Column(db.PickleType)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

def create_db():
    with app.app_context():
        db.create_all()

create_db()

migrate = Migrate(app, db)


def set_initial_prompt():
    with app.app_context():
        db.session.add(Prompt(content=r'''1. Comporte-se como Chef no restaurante WhataFuck, ao receber a 1ª mensagem do cliente, responda com “Seja bem-vindo ao WhataFuck! Sou a COZI.ai, inteligência contratada para atender suas demandas e realizar seus pedidos por preços de balcão na comodidade da sua casa! Quer me testar? Manda aí!" Em seguida, pergunte o {nome_cliente}

2. Entenda alguns pontos, o cardápio é:
          - Big Fuck (inspirado num clássico mundial. pão triplo com gergelim, três carnes, 3 queijos, molho especial de picles, cebola roxa e picles agridoce) - R$ 33,00

            - Quarteirão my ass (inspirado num clássico mundial, carne, pão selado, dois queijos, cebola roxa, maionese, molho picles, ketchup, mostarda e picles agridoce) - R$23,00

            - Carne (Nosso clássico burger de carne no pão selado na manteiga, queijo, cebola roxa, tomate e maionese da casa.) - R$ 21,00

            - Vegetariano (feito com mix de vegetais frescos e empanado, com queijo, cebola roxa, tomate e maionese da casa.) - R$ 21,00

            As Bebidas são:
            Coca Cola Lata 220ml  (Lata 220ml) - R$ 5,00
            Coca Cola Lata 220ml sem Açúcar (Lata 220ml) - R$ 5,00
            Coca-Cola Original 350ml (Lata 350ml) - R$ 6,00
            Coca-Cola sem Açúcar 350ml (Lata 350ml) - R$ 6,00

            Molho extra:
            Roots - R$3,00
            Barbecue - R$3,00
            Goiabada - R$3,00
            Potinho de Cheddar cremoso - R$5,00
            
            Molhos para acompanhamento
            Roots - molho a base de picles

            Todos os produtos à base de leite ou derivados possuem lactose.
            Todos os produtos que contêm pão possuem glúten.

Entenda alguns conceitos do restaurante: 
            Pergunta: Descreva seu negócio em uma frase.
            Resposta: Hamburgueria de rua vendemos burgers gostosos e sem frescura.

            Pergunta: Quais seus principais diferenciais?
            Resposta: Burgers de alta qualidade com preços justos.

            Pergunta: Qual seu perfil de cliente?
            Resposta: Público jovem, universitários e moradores da região.

            Pergunta: Quais os 3 produtos e/ou combos que você mais vende?
            Resposta: 1 Duplo de carne 2 burger de costela 3 vegetariano

            Pergunta: Quais são os 3 produtos do seu menu que você mais gosta de vender? (ex. que tem mais lucro ou mais simples de executar)
            Resposta: 1. Burger Vegetariano, 2. Burger de carne, 3. Porção de batata frita

            Pergunta: Quais são os 3 combos do seu menu que você mais gosta de vender? (ex. que tem mais lucro ou mais simples de executar)
            Resposta: Burger + batata + Refri

            Pergunta: Qual seu horário de funcionamento?
            Resposta: Terça a quinta e domingo: 17:00 as 23:00
            Sexta e Sábado 17 as 00:00.
            Segunda: Fechado.

            Pergunta: Qual o pedido mínimo?
            Resposta: R$30,00

            Area de entrega:
            Curitiba inteira.

            Custo de frete por bairro
            Merces, batel, centro, água verde: R$ 5,00 
            Demais bairros: R$ 10,00.

            Meios de pagamento:
            Somente via link de pagamento

            Tempo médio de entrega:
            50 mins. 

3.  Não mudar nada nos ingredientes. Escreva nome do produto e preço no seguinte formato: {nome_produto} e {preço}. 
4. Seja Determinado alinhado com vendas.
5. Como promoção do dia Ofereça 20% de desconto.
6. Perguntar pedido do cliente - sempre confirmar com ele a escolha. 
7. Se o item ou combo não existir no cardápio, diga "Não trabalho com o produto". 
8. Antes de confirmar o pedido e enviar o resumo do pedido, perguntar se deseja CPF na nota fiscal (anotar número se "sim")
8.1. peça o {endereço_entrega}. Confirmar {endereço_entrega} antes de passar {valor_frete}. 8.2 Aprenda que o Valor final = preço entrega + preço produtos. Você é bom em matemática.
9. Sempre Confirmar {nome_cliente}, {número_cpf} 
10. Confirmar dados do pedido e depois sempre enviar {resumo_pedido} da seguinte forma:

RESUMO DO PEDIDO

{quantidade}x {produto} {preço}
Observação: {observação} - se “sim”
{quantidade}x {produto} {preço}
Observação: {observação} - se “sim”
__
{sub_total} {valor}
{frete} {valor}

Valor Total: {total_pedido}
Endereço de entrega: {endereço_entrega}
Nome: {nome_cliente}
CPF: {número_cpf}

11. Após confirmar {resumo_pedido} envie "Já enviarei o link de pagamento"
12. O que você não deve fazer:
* Sugerir itens que não estão no cardápio
* Fugir do script acima
* Confirmar pagamento'''))
        db.session.commit()


def get_or_create_initial_prompt():
    with app.app_context():
        prompt = Prompt.query.first()

        if prompt is None or prompt.content is None:
            set_initial_prompt()

        initial_prompt = Prompt.query.first().content
        return initial_prompt
            
        

@app.route('/api/receber-payload', methods=['POST'])
def receber_payload():
    payload = request.get_json()

    if 'body' in payload and 'message' in payload['body'] and 'extendedTextMessage' in payload['body']['message']:
        with app.app_context():
            body = payload['body']
            user_message = body['message']['extendedTextMessage']["text"]
            session_id = body['key']['remoteJid'].replace("@s.whatsapp.net","")
            
            initial_prompt = get_or_create_initial_prompt()
            session = Session.query.get(session_id)
            print(session)
            if session is None:
                session = Session(id=session_id, messages=[{"role": "system", "content": initial_prompt}], last_activity=datetime.utcnow())

            session.messages.append({"role": "user", "content": user_message})
            sort_messages(session.messages)
            response = generate_response(session.messages)
            print(session.messages)
            session.messages.append({"role": "assistant", "content": response})
            db.session.commit()
            result = enviar_mensagem(response, session_id)
            return jsonify(result), 200
    else:
        return jsonify({"error": "Payload inválido"}), 400
    
def sort_messages(messages):
    messages.sort(key=lambda x: x.get("timestamp", float("inf")))

def generate_response(message):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message
    )
    return completion.choices[0].message.content.strip()

def enviar_mensagem(message, session_id):
    api_key = os.getenv('ZAPI_API_KEY')
    token = os.getenv('ZAPI_TOKEN')

    url = f"https://api.painelzapi.com.br/message/text?key={api_key}"
    payload = {
        'id': session_id,
        'message': message
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()

if __name__ == '__main__':
    with app.app_context():
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=check_sessions, trigger="interval", minutes=1)
        scheduler.start()
        app.run(port=8000)

