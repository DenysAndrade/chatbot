import pandas as pd
import requests
import time
import re


SERVER_URL = "http://localhost:3000"
EXCEL_PATH = "Enviar.xlsx"
DELAY_ENTRE_CONTATOS = 5


def formatar_numero(numero):
    numero_limpo = re.sub(r'\D', '', str(numero))
    if not numero_limpo.startswith('55'):
        numero_limpo = '55' + numero_limpo
    return f"{numero_limpo}@c.us"

def verificar_numero(chat_id):
    try:
        numero_limpo = ''.join(filter(str.isdigit, chat_id.split('@')[0]))
        
        response = requests.get(
            f"{SERVER_URL}/check-number",
            params={'chatId': numero_limpo},
            timeout=25
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['registered'], data.get('whatsappId')
            
        print(f"Erro na API: {response.status_code} - {response.text}")
        return False, None
        
    except Exception as e:
        print(f"Erro de conexão: {str(e)}")
        return False, None

# Carregar dados ANTES do loop principal
try:
    df = pd.read_excel(EXCEL_PATH)
    print("\n✅ Planilha carregada com sucesso!")
    print("Amostra dos dados:")
    print(df.head(3))
except Exception as e:
    print(f"\n❌ ERRO CRÍTICO: Falha ao ler Excel\n{str(e)}")
    exit()

# Processamento principal
for index, row in df.iterrows():
    try:
        numero_original = row['Número']
        pessoa = row['Pessoa']
        mensagem = row['Mensagem']
        
        # Formatar número
        chat_id = formatar_numero(numero_original)
        if not chat_id:
            print(f"⚠️ Número inválido: {numero_original}")
            continue
            
        # Verificar registro
        valido, numero_formatado = verificar_numero(chat_id)
        if not valido:
            print(f"🚫 Número não registrado: {numero_formatado}")
            continue
            
        # Enviar mensagem
        response = requests.post(
            f"{SERVER_URL}/send-message",
            json={"chatId": chat_id, "message": f"🎉 É amanhã, {pessoa}! {mensagem} 🔥\n \n✨ A maior e verdadeira *FOLIA DE OFERTAS* da região está no ar! ✨\n \n✅ Descontos imperdíveis!\n✅ Frete grátis no raio de 120kM para você economizar ainda mais!\n✅ Varios produtos com preços que você só encontra aqui!\n \n⏳ Não deixe pra depois, os estoques são limitados e as ofertas são válidas do dia *21/02/2025* até *06/03/2025* viu!\nDigite *1* e faça ja seu orçamento! 😁"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Falha no envio: {response.text}")
            continue
            
        # Enviar PDF
        response_pdf = requests.post(
            f"{SERVER_URL}/send-pdf",
            json={"chatId": chat_id},
            timeout=30
        )
        
        if response_pdf.status_code == 200:
            print(f"✅ Envio completo para {pessoa}")
        else:
            print(f"⚠️ PDF não enviado: {response_pdf.text}")
            
    except Exception as e:
        print(f"🔥 Erro no contato {numero_original}: {str(e)}")
    
    finally:
        time.sleep(DELAY_ENTRE_CONTATOS)

print("\n🎉 Processo finalizado com sucesso!")
