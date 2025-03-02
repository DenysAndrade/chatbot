from time import sleep, time
import requests
import os 
CONFIRMAR_DISPARO = 'confirmar_disparo'

SERVER_URL = "http://localhost:3000"
user_blocked = {}
user_blocked_1 = {}
feedback_pending = {}
unrecognized_count = {}
colaboradores = {}  
administradores = {}  
employee_state = {}  


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

def handle_blocked_collaborator(chat_id, text):
    block_data = user_blocked_1.get(chat_id)
    if not block_data:
        return False
    
    current_time = time()
    
    # Se enviar qualquer mensagem, cancela o bloqueio
    del user_blocked_1[chat_id]
    send_message(chat_id, "🔓 Bloqueio de colaborador removido. Pode continuar operando.")
    return True

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
        

    }
    
     
    if chat_id in administradores and text.startswith('/admin'):
        handle_admin_commands(chat_id, text)
        return

    # Registro de colaborador
    if text.isdigit() and len(text) == 6 and chat_id not in colaboradores:
        colaboradores[chat_id] = text
        send_message(chat_id, f"✅ Registrado como colaborador #{text}\n{EMPLOYEE_MENU}")
        if chat_id in administradores:
            send_message(chat_id, ADMIN_MENU)
        return

    # Processamento para colaboradores registrados
    if chat_id in colaboradores:
        handle_employee_flow(chat_id, text, sender_name)
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

EMPLOYEE_MENU = """👷♂️ *MENU COLABORADOR* 👷♀️
    Escolha uma opção:
1️⃣ - Solicitar transferência entre filiais
2️⃣ - Fazer pedido de compra
3️⃣ - Reportar produtos em falta
0️⃣ - Sair do modo colaborador"""

ADMIN_MENU = """🔧 *MENU ADMINISTRADOR* 🔧
Opções adicionais:
4️⃣ - Listar colaboradores (admin)
5️⃣ - Remover colaborador (admin)
6️⃣ - Exportar dados de colaboradores
7️⃣ - Limpar todos os registros
8️⃣ - Disparo em massa"""


def on_message_colaborador(message):
    chat_id = message.get('from', '')
    sender_name = message.get('sender', {}).get('pushname', '')
    message_type = message.get('type', '').lower()
    text = message.get('body', '').strip().lower()

    if chat_id in user_blocked_1:
        if handle_blocked_collaborator(chat_id, text):
            return
        else:
            return


def handle_employee_flow(chat_id, text, sender_name):
    if text == '0':
        del colaboradores[chat_id]
        # Limpeza de estados
        if chat_id in employee_state:
            del employee_state[chat_id]
        if chat_id in user_blocked_1:
            del user_blocked_1[chat_id]
            
        send_message(chat_id, "🚪 Modo colaborador desativado.")
        # Envia o menu do cliente corretamente
        send_message(chat_id, on_message().format(sender_name=sender_name))
        return True

    if text == '1':
        send_message(chat_id, "📦 Para transferência, informe:\nCódigo do produto | Quantidade | Filial origem | Filial destino")
        send_message(chat_id, "*OBSERVACÕES IMPORTANTES:*\n \n> *AS SOLICITACÕES DE TRANSFERÊNCIA DEVEM SER REALIZADAS ATE AS 15H DO DIA.*\n \n> *PEDIDOS FEITOS APOS AS 15H, SO SERÃO SOLICITADOS NO DIA SEGUINTE.*\n \n> *CASO HAJA URGÊNCIA DE PEDIDO, FAVOR IR ATE O BALCÃO DE ATENDIMENTO E REALIZAR AVISO, JUNTAMENTE COM AUTORIZACÃO DA GERENCIA.*\n \n> *VENDEDORES DEVEM FICAR ATENTOS AOS PEDIDOS, SEMPRE BUSCANDO ATUALIZACÃO COM O ATENDENTE.*")
        send_message(chat_id, "Boas vendas!! 🤗")
        employee_state[chat_id] = 'aguardando_transferencia'
        user_blocked_1[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
        
    elif text == '2':
        send_message(chat_id, "🛒 Para pedido de compra, informe:\nNome do produto | Quantidade | Justificativa")
        employee_state[chat_id] = 'aguardando_pedido'
        user_blocked_1[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
        
    elif text == '3':
        send_message(chat_id, "⚠️ Liste os produtos em falta (separados por vírgula):")
        employee_state[chat_id] = 'aguardando_faltantes'
        user_blocked_1[chat_id] = {'blocked_at': time(), 'apology_sent': False}
        unrecognized_count[chat_id] = 0  # Reseta contador
        return
        
    elif text == '4' and chat_id in administradores:
        listar_colaboradores(chat_id)
        
    elif text == '5' and chat_id in administradores:
        send_message(chat_id, "Digite o Chat ID do colaborador a ser removido:")
        employee_state[chat_id] = 'aguardando_remocao'

    elif text == '8' and chat_id in administradores:
        send_message(chat_id, "⚠️ *CONFIRMAR DISPARO EM MASSA* ⚠️\n\nDigite *CONFIRMAR* para iniciar o envio")
        employee_state[chat_id] = CONFIRMAR_DISPARO
        return True
    
    # Adicione este novo caso para tratar a confirmação
    elif employee_state.get(chat_id) == CONFIRMAR_DISPARO:
        from envio import run_envio
        if text == 'confirmar':
            try:
                send_message(chat_id, "📢 Iniciando disparo em massa...")
                resultado = run_envio()  # Executa o disparo
                
                if resultado:
                    send_message(chat_id, f"✅ Disparo concluído!\nMensagens enviadas: {resultado}")
                else:
                    send_message(chat_id, "❌ Nenhuma mensagem enviada. Verifique o arquivo de destinatários.")
                    
            except Exception as e:
                send_message(chat_id, f"⚠️ Erro no disparo: {str(e)}")
            
            del employee_state[chat_id]
            return True
        
        else:
            send_message(chat_id, "❌ Disparo cancelado")
            del employee_state[chat_id]
            return True
        
    elif text == "Obrigado": 
        send_message(chat_id, "A Home Center Tupan agradece seu contato, ficaremos à sua disposição, qualquer coisa só chamar 🤗\n \nAte mais! ❤️💙💛")
    else:
        menu = EMPLOYEE_MENU
        if chat_id in administradores:
            menu += "\n" + ADMIN_MENU
        send_message(chat_id, f"❌ Opção inválida")
    

def handle_employee_state(chat_id, text):
    estado = employee_state[chat_id]
    
    if estado == 'aguardando_faltantes':
        produtos = [p.strip() for p in text.split(',')]
        send_message(chat_id, f"✅ Faltantes registrados:\n{', '.join(produtos)}")
        del employee_state[chat_id]
        
    elif estado == 'aguardando_remocao':
        if text in colaboradores:
            del colaboradores[text]
            send_message(chat_id, f"❌ Colaborador {text} removido!")
        else:
            send_message(chat_id, "❌ Chat ID não encontrado!")
        del employee_state[chat_id]
        
    # Adicione handlers para outros estados conforme necessário
    send_message(chat_id, EMPLOYEE_MENU)

def listar_colaboradores(chat_id):
    if not colaboradores:
        send_message(chat_id, "📭 Nenhum colaborador registrado!")
        return
        
    lista = "📋 *Colaboradores Registrados:*\n"
    for cid, mat in colaboradores.items():
        lista += f"- {mat} ({cid})\n"
    send_message(chat_id, lista)

def handle_admin_commands(chat_id, text):
    if 'exportar' in text:
        # Implemente exportação para CSV
        send_message(chat_id, "📤 Exportando dados...")
        
    elif 'limpar' in text:
        colaboradores.clear()
        send_message(chat_id, "♻️ Todos os colaboradores foram removidos!")
        
    send_message(chat_id, ADMIN_MENU)


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