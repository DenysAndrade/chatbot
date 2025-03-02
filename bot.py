from time import sleep, time
import requests
import os 

SERVER_URL = "http://localhost:3000"
user_blocked = {}
user_blocked_1 = {}
feedback_pending = {}
unrecognized_count = {}


PDF_PROMOCOES = os.path.join(os.path.dirname(__file__), 'assets', 'promocoes.pdf')

UNRECOGNIZED_RESPONSES = [
    "🤔 Desculpe, não entendi o que vc falou.\n \nPara facilitar seu atendimento, digite *3* para falar com nosso atendente 🧑🏻‍💻, ou *MENU* 📲",
    "😐 *Ainda não tenho certeza em como posso te ajudar...*\n \nQue tal a gente fazer assim: vc pode escrever de novo aqui pra mim o que necessita , só que em outras palavras, pra ver se eu consigo entender dessa vez.\n \nAh, e também dá para digita *MENU* e escolhes uma das opcões",
    "😕 Que pena que não tô conseguindo te ajudar por aqui.\n \nTive uma ideia: você pode digita *3* e nosso atendente ja vai te atender.\n \nTenho certeza que ele ira solucionar sua duvida\n \nAh, e lembra que sempre dá pra dititar *MENU* e escolher um assunto, tá?👇"
]

def send_file(chat_id, file_path):
    try:
        # Verificação completa do arquivo
        if not os.path.exists(file_path):
            print(f"ERRO: Arquivo não encontrado em {file_path}")
            return False

        # Envia o arquivo via multipart/form-data
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file.read())}
            data = {'chatId': chat_id}
            
            response = requests.post(
                f"{SERVER_URL}/send-file",
                files=files,
                data=data,
                timeout=15
            )

            if response.status_code == 200:
                print("PDF enviado com sucesso!")
                return True
            else:
                print(f"Erro ao enviar PDF: {response.status_code}")
                return False

    except Exception as e:
        print(f"Erro crítico ao enviar arquivo: {str(e)}")
        return False

def send_message(chat_id, message):
    try:
        print(f" Tentando enviar mensagem para {chat_id}: {message[:50]}...")
        response = requests.post(
            f"{SERVER_URL}/send-message",
            json={"chatId": chat_id, "message": message},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Mensagem enviada com sucesso!")
            return True
        else:
            print(f" Erro {response.status_code} ao enviar mensagem")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f" Erro de conexão: {str(e)}")
        return False
    except Exception as e:
        print(f" Erro inesperado: {str(e)}")
        return False

def get_unread_messages():
    try:
        response = requests.get(f"{SERVER_URL}/unread-messages", timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"Erro ao buscar mensagens: {e}")
        return []

def handle_blocked_user(chat_id, text):
    block_data = user_blocked.get(chat_id)
    if not block_data:
        return False
    current_time = time()
    
    if text == "6":
        send_message(chat_id, "Retomando seu atendimento virtual!")
        del user_blocked[chat_id]
        print(f"Usuário {chat_id} desbloqueado via comando")
        return True
    
    if (current_time - block_data['blocked_at']) >= 60:
        if not block_data['apology_sent']:
            send_message(chat_id, "Peço desculpas, vi aqui que você ainda não foi respondido pelo nosso atendente 😔.\nDigite 3, para retornar à fila de espera.")
            user_blocked[chat_id]['apology_sent'] = True
        del user_blocked[chat_id]
        print(f"Usuário {chat_id} desbloqueado por timeout")
        return True
    
    print(f"Ignorando mensagem bloqueada de {chat_id}")
    return False

def handle_blocked_collaborator(chat_id):
    block_data = user_blocked_1.get(chat_id)
    if not block_data:
        return False
    current_time = time()
    
    if (current_time - block_data['blocked_at']) >= 30:
        if not block_data['apology_sent']:
            user_blocked_1[chat_id]['apology_sent'] = True
        del user_blocked_1[chat_id]
        print(f"Usuário {chat_id} desbloqueado por timeout")
        return True
    
    print(f"Ignorando mensagem bloqueada de {chat_id}")
    return False

def on_message(message):
    chat_id = message.get('from', '')
    sender_name = message.get('sender', {}).get('pushname', '')
    message_type = message.get('type', '').lower()

    if message_type == 'audio':
        print(f"Áudio recebido de {sender_name} ({chat_id})")
        send_message(chat_id, "🎵 Olá {sender_name}!\n \nPor questões de segurança, vamos direcionar você para nosso atendente.\n \n⏳ Aguarde um momento!")
        user_blocked[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0
        return
    text = message.get('body', '').strip().lower()
    
    if not chat_id or not text:
        return

    print(f"Mensagem de {sender_name} ({chat_id}): {text}")

    if chat_id in feedback_pending:
        print(f"Processando feedback para {chat_id}")
        try:
            if send_message(chat_id, f"🌟 Obrigado pelo seu feedback {sender_name}! Sua opinião nos ajuda a melhorar cada dia mais!"):
                print("✅ Agradecimento enviado com sucesso")
            else:
                print(" Falha ao enviar agradecimento")
        except Exception as e:
            print(f"Erro crítico ao enviar agradecimento: {str(e)}")
        finally:
            del feedback_pending[chat_id]
            print(f"Estado de feedback limpo para {chat_id}")
        return  # Sai após processar o feedback

    if chat_id in user_blocked:
        if handle_blocked_user(chat_id, text):
            return
        else:
            return

    respostas = {
        "menu": f"👋 Oi {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "oi": f"👋 Oi {sender_name}!\n \n 🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "olá": f"👋 Olá {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "ola": f"👋 Olá {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada. \n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "bom dia": f"👋 Bom dia {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "boa tarde": f"👋 Boa tarde {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "boa noite": f"👋 Boa noite {sender_name}!\n \n🤖 Sou o Tupanzinho assistente virtual da Home Center Tupan de Serra Talhada.\n \nDigita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "1": f"Aqui está {sender_name}, o contato de alguns de nossos vendedores, eles tiraram suas dúvidas e passaram o orçamento do seu produto: 🤩\n \n📞Bruno Simões: 87 99946-2496 \n 📞 Leciano: 87 99913-4861\n 📞 Suellen: 87 99983-9138 \n \nFicarei à disposição para qualquer dúvida! qualquer coisa só chamar 🤗",
        "2": f"🔥 Compre agora {sender_name}!\n \n📅 Promoção válida até *06/03/2025* ou enquanto durar o estoque.\n \nDigite *1* e solicite ja seu orçamento! 🤩",
        "3": f"⏳ Aguarde um momento, um atendente irá responder em breve {sender_name}!\nCaso queira retornar ao menu, digite 6.",
        "4": f"{sender_name},  peço que envie o comprovante em *PDF* ou *IMAGEM*, onde apareça todas as informações do mesmo, juntamente com o *CPF* do titular da ficha.\nPara melhor identificação e agilidade no processo.\n \nEm caso de duvida, digite *3* e fale com o nosso atendente! 😉",
        "6": f"{sender_name}, digita aqui pra mim o que vc precisa? Ou então, é só digita uma das opção 😉:\n*1️⃣ - Orçamento.*\n*2️⃣ - Promoções da semana.*\n*3️⃣ - Falar com nosso atendente.*\n*4️⃣ - Enviar comprovante de pagamento*\n*5️⃣ - Feedbacks*",
        "5": "Seu feedback e muito importante para nós. 🥰\n \nDeixe aqui seu comentario, como foi sua experiencia de compra aqui na Tupan, e se achou todos os produtos que estava procurando. 🌟",
        "parcela": "⏳ Aguarde um momento, um atendente irá responder em breve!\nCaso queira retornar ao menu, digite 6.",
        "pagamento": "⏳ Aguarde um momento, um atendente irá responder em breve!\nCaso queira retornar ao menu, digite 6.",
        "obrigado": "🥰 A Home Center Tupan agradece seu contato, ficaremos à sua disposição, qualquer coisa só chamar 🤗\n \nAte mais! ❤️💙💛",
        "obrigada": "🥰 A Home Center Tupan agradece seu contato, ficaremos à sua disposição, qualquer coisa só chamar 🤗\n \nAte mais! ❤️💙💛", 
        "👍🏼": "🥰 A Home Center Tupan agradece seu contato, ficaremos à sua disposição, qualquer coisa só chamar 🤗\n \nAte mais! ❤️💙💛",
        "🫱🏻‍🫲🏻": "🥰 A Home Center Tupan agradece seu contato, ficaremos à sua disposição, qualquer coisa só chamar 🤗\n \nAte mais! ❤️💙💛", 
        "1025": "👋 Olá colaborador, pelo que vi aqui, vc esta querendo realizar uma transferência de produtos entre filiais.\n \nPara isso, preciso que vc me envie as seguintes informações:\n \nCodigo reduzido do produto:\nQuantidade:\nFilial de saida e filial de destino:",
        "1026": "👋 Olá colaborador, pelo que vi aqui, vc esta querendo realizar a solicitacão de materiais para consumo.\nPara isso, preciso que vc me envie as seguintes informações:\n \nNome do produto:\nQuantidade:\nDestinacão para qual setor:",


    }
    if text == "1025":
        print(f"Colaborador {chat_id} bloqueado para realizar transferencia")
        send_message(chat_id, respostas["1025"])
        send_message(chat_id, "*OBSERVACÕES IMPORTANTES:*\n \n*> AS SOLICITACÕES DE TRANSFERÊNCIA DEVEM SER REALIZADAS ATE AS 15H DO DIA*.\n \n*> PEDIDOS FEITOS APOS AS 15H, SO SERÃO SOLICITADOS NO DIA SEGUINTE.*\n \n*> CASO HAJA URGÊNCIA DE PEDIDO, FAVOR IR ATE O BALCÃO DE ATENDIMENTO E REALIZAR AVISO, JUNTAMENTE COM AUTORIZACÃO DA GERENCIA.*\n \n*> VENDEDORES DEVEM FICAR ATENTOS AOS PEDIDOS, SEMPRE BUSCANDO ATUALIZACÃO COM O ATENDENTE.*")
        send_message(chat_id, "Caso necessite realizar outra transferência durante o dia, so digitar *1025*\n \nBoas vendas!! 🤗")
        user_blocked_1[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
    if text == "1026":
        print(f"Colaborador {chat_id} bloqueado para realizar transferencia")
        send_message(chat_id, respostas["1026"])
        send_message(chat_id, "*OBSERVACÕES IMPORTANTES:*\n \n*> AS SOLICITACÕES DEVEM SER FEITAS ATE O DIA 05 DE CADA MÊS*")
        send_message(chat_id, "Caso necessite editar a lista, so digitar *1026*\n \nBom trabalho!! 🤗")
        user_blocked_1[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
    
    if text == "2":
        send_file(chat_id, PDF_PROMOCOES)

    if text == "3":
        print(f"Usuário {chat_id} bloqueado para atendimento")
        send_message(chat_id, respostas["3"])
        user_blocked[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
    
    if text == "4":
        print(f"Usuário {chat_id} bloqueado para atendimento")
        send_message(chat_id, respostas["4"])
        user_blocked[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return

    if text == "5":
        print(f"\n⚡ Comando '5' recebido de {chat_id}")
        success = send_message(chat_id, respostas["5"])
        
        if success:
            print(f"🔄 Ativando modo feedback para {chat_id}")
            feedback_pending[chat_id] = True
        else:
            print(f"💥 Falha crítica: Não foi possível ativar o feedback para {chat_id}")
            send_message(chat_id, "⚠️ Ops! Tivemos um problema. Tente novamente mais tarde.")
        return
        
    elif text in respostas:
        send_message(chat_id, respostas[text])
        unrecognized_count[chat_id] = 0  
        return

    # Trata mensagens não reconhecidas
    count = unrecognized_count.get(chat_id, 0)
    response_index = count % len(UNRECOGNIZED_RESPONSES)
    
    # Formata a mensagem com o nome do usuário
    response = UNRECOGNIZED_RESPONSES[response_index].format(nome=sender_name)
    
    send_message(chat_id, response)
    unrecognized_count[chat_id] = count + 1 
   

def main():
    print("Bot iniciado. Aguardando mensagens...")
    while True:
        try:
            messages = get_unread_messages()
            for msg in messages:
                try:
                    on_message(msg)
                except Exception as e:
                    print(f"Erro: {e}")
            sleep(3)
        except KeyboardInterrupt:
            print("\nDesligando...")
            break
        except Exception as e:
            print(f"Erro crítico: {e}")
            sleep(5)

if __name__ == "__main__":
    main()