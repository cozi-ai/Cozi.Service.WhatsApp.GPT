from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import openai
import requests
import os

app = Flask(__name__)

# Configurando as chaves da API do OpenAI
openai.api_key = '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'
ZAPI_API_KEY='key-ZAPIbu2Pa4kRNYERRSR'
ZAPI_TOKEN='23273712'
# Configurando a conexão com o banco de dados usando SQLAlchemy
database_url = 'sqlite:///chatbot.db'  # URL de conexão com o banco de dados SQLite
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Definindo o modelo para a tabela de sessões
class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    session_id = Column(String, primary_key=True)
    prompt = Column(Text)

# Cria a tabela no banco de dados se ainda não existir
Base.metadata.create_all(engine)

# Definindo a rota para receber as mensagens do WhatsApp
@app.route('/api/receber-payload', methods=['POST'])
def whatsapp():
    payload = request.get_json()
    print(payload)

    if 'body' in payload and 'message' in payload['body']:
        with app.app_context():
            body = payload['body']
            message_body = body['message']
            session_id = body['key']['remoteJid'].replace("@s.whatsapp.net", "")

        if 'extendedTextMessage' in message_body:
            user_message = message_body['extendedTextMessage'].get("text", "")
        elif 'conversation' in message_body and isinstance(message_body['conversation'], dict):
            user_message = message_body['conversation'].get("text", "")
        else:
            user_message = ""


        # Obtém o prompt da sessão do banco de dados ou cria um novo
        prompt = get_prompt(session_id)
        prompt.append({"role": "user", "content": "{}".format(user_message)})

        # Chamando a função para gerar a resposta do chatbot
        response = generate_response(prompt)

        prompt.append({"role": "assistant", "content": "{}".format(response)})

        # Salva o prompt atualizado no banco de dados
        save_prompt(session_id, prompt)

        result = enviar_mensagem(response, session_id)
        return jsonify(result), 200
    else:
        return jsonify({"error": "Payload inválido"}), 400

# Função para gerar a resposta do chatbot usando a API do OpenAI
def generate_response(message):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message
    )
    return completion.choices[0].message.content.strip()

# Função para enviar a mensagem para o número de telefone usando a API do Z-API
def enviar_mensagem(message, session_id):
    api_key = ZAPI_API_KEY
    token = ZAPI_TOKEN

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

initial_prompt = '''1. Comporte-se como Chef no restaurante WhataFuck, ao receber a 1ª mensagem do cliente, responda com “Seja bem-vindo ao WhataFuck! Sou a COZI.ai, inteligência contratada para atender suas demandas e realizar seus pedidos por preços de balcão na comodidade da sua casa! Quer me testar? Manda aí!" Em seguida, pergunte o {nome_cliente}

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
* Confirmar pagamento'''
# Função para obter o prompt da sessão do banco de dados
def get_prompt(session_id):
    session = Session()
    chat_session = session.query(ChatSession).filter_by(session_id=session_id).first()
    if chat_session is None:
        return [{"role": "system", "content": initial_prompt}]
    return eval(chat_session.prompt)

# Função para salvar o prompt no banco de dados
def save_prompt(session_id, prompt):
    session = Session()
    chat_session = session.query(ChatSession).filter_by(session_id=session_id).first()
    if chat_session is None:
        chat_session = ChatSession(session_id=session_id, prompt=str(prompt))
    else:
        chat_session.prompt = str(prompt)
    session.add(chat_session)
    session.commit()

# Rodando a aplicação Flask
if __name__ == '__main__':
    app.run()