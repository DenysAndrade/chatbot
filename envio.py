import pandas as pd
import requests
import time
import re
import os
from bot import TEXTO_MENSAGEM

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

def verificar_interrupcao():

    return os.path.exists("interromper.txt")

def run_envio_PDF(TEXTO_MENSAGEM):
    
    try:
        if verificar_interrupcao():
            os.remove("interromper.txt")
            
        print("\n📊 Carregando planilha...")
        df = pd.read_excel(EXCEL_PATH)
        total_contatos = len(df)
        enviados_com_sucesso = 0
        
        print(f"✅ Planilha carregada | Total de contatos: {total_contatos}")
        print("-----------------------------------------")
        
        for index, row in df.iterrows():
            if verificar_interrupcao():
                print("\n⏹️ Disparo interrompido pelo usuário!")
                return "Operação interrompida manualmente!"
            
            numero = row['Número']
            pessoa = row['Pessoa']
            mensagem = row['Mensagem']
            
            try:
                print(f"\n📤 Processando {index+1}/{total_contatos}: {pessoa}")
                
                # Formatação do número
                chat_id = formatar_numero(numero)
                if not chat_id:
                    print(f"⚠️ Número inválido: {numero}")
                    continue
                
                # Envio da mensagem principal
                # Monta a mensagem final
                mensagem_final = (f"Oii {pessoa}, {mensagem}\n\n"  + "".join([list(item.values())[0] for item in TEXTO_MENSAGEM]))
                
                # Envio da mensagem principal
                resposta_mensagem = requests.post(
                    f"{SERVER_URL}/send-message",
                    json={
                        "chatId": chat_id,
                        "message": mensagem_final
                    },
                    timeout=30
                )
                
                if resposta_mensagem.status_code != 200:
                    print(f"❌ Falha no envio: {resposta_mensagem.text}")
                    continue
                
                # Envio do PDF
                resposta_pdf = requests.post(
                    f"{SERVER_URL}/send-pdf",
                    json={"chatId": chat_id},
                    timeout=30
                )
                
                if resposta_pdf.status_code == 200:
                    enviados_com_sucesso += 1
                    print(f"✅ Enviado para {pessoa}")
                else:
                    print(f"⚠️ PDF não enviado: {resposta_pdf.text}")
                    
            except Exception as e:
                print(f"🔥 Erro crítico: {str(e)}")
                
            finally:
                time.sleep(DELAY_ENTRE_CONTATOS)
        
        print("\n-----------------------------------------")
        print(f"🎉 Disparo concluído! | Sucessos: {enviados_com_sucesso}/{total_contatos}")
        return f"Total de mensagens enviadas: {enviados_com_sucesso}"
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return f"Erro no disparo: {str(e)}"

def run_envio_mensegem():
    try:
        if verificar_interrupcao():
            os.remove("interromper.txt")
            
        print("\n📊 Carregando planilha...")
        df = pd.read_excel(EXCEL_PATH)
        total_contatos = len(df)
        enviados_com_sucesso = 0
        
        print(f"✅ Planilha carregada | Total de contatos: {total_contatos}")
        print("-----------------------------------------")
        
        for index, row in df.iterrows():
            if verificar_interrupcao():
                print("\n⏹️ Disparo interrompido pelo usuário!")
                return "Operação interrompida manualmente!"
            
            numero = row['Número']
            pessoa = row['Pessoa']
            mensagem = row['Mensagem']
            
            try:
                print(f"\n📤 Processando {index+1}/{total_contatos}: {pessoa}")
                
                # Formatação do número
                chat_id = formatar_numero(numero)
                if not chat_id:
                    print(f"⚠️ Número inválido: {numero}")
                    continue
                
                # Envio da mensagem principal
                resposta_mensagem = requests.post(
                    f"{SERVER_URL}/send-message",
                    json={
                        "chatId": chat_id,
                        "message": (
                            f"Oii {pessoa}, {mensagem}\n\n"
                            "✨ Vim te avisar que a semana do consumidor está chegando ✨\n\n"
                            "✅ Descontos imperdíveis!\n"
                            "✅ Frete grátis no raio de 120kM\n"
                            "✅ Preços exclusivos!\n\n"
                            "⏳ Melhor hora para comprar!\n"
                            "Digite *1* para orçamento! 😁"
                        )
                    },
                    timeout=30
                )

            except Exception as e:
                print(f"🔥 Erro crítico: {str(e)}")
                
            finally:
                time.sleep(DELAY_ENTRE_CONTATOS)
                
                if resposta_mensagem.status_code != 200:
                    print(f"❌ Falha no envio: {resposta_mensagem.text}")
                    continue

    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return f"Erro no disparo: {str(e)}"
    
def run_envio_midia():
    try:
        if verificar_interrupcao():
            os.remove("interromper.txt")
            
        print("\n📊 Carregando planilha...")
        df = pd.read_excel(EXCEL_PATH)
        total_contatos = len(df)
        enviados_com_sucesso = 0
        
        print(f"✅ Planilha carregada | Total de contatos: {total_contatos}")
        print("-----------------------------------------")
        
        for index, row in df.iterrows():
            if verificar_interrupcao():
                print("\n⏹️ Disparo interrompido pelo usuário!")
                return "Operação interrompida manualmente!"
            
            numero = row['Número']
            pessoa = row['Pessoa']
            mensagem = row['Mensagem']
            caminho_midia = row['CaminhoMidia']
            tipo_midia = row['TipoMidia']
            descricao = row['Descricao']
            
            try:
                print(f"\n📤 Processando {index+1}/{total_contatos}: {pessoa}")
                
                # Formatação do número
                chat_id = formatar_numero(numero)
                if not chat_id:
                    print(f"⚠️ Número inválido: {numero}")
                    continue
                
                # Envio da mensagem principal
                try:
                    resposta_mensagem = requests.post(
                        f"{SERVER_URL}/send-message",
                        json={
                            "chatId": chat_id,
                            "message": f"Oii {pessoa}, {mensagem}"
                        },
                        timeout=30
                    )
                    resposta_mensagem.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"❌ Falha no envio da mensagem: {str(e)}")
                    continue
                
                # Determina o endpoint
                endpoint = '/send-image' if tipo_midia.lower() == 'imagem' else '/send-video'
                
                # Envio da mídia com tratamento aprimorado
                try:
                    resposta_midia = requests.post(
                        f"{SERVER_URL}{endpoint}",
                        json={
                            "chatId": chat_id,
                            "filePath": caminho_midia,
                            "caption": descricao
                        },
                        timeout=60
                    )
                    resposta_midia.raise_for_status()
                    enviados_com_sucesso += 1
                    print(f"✅ Mídia enviada para {pessoa}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Falha no envio da mídia: {str(e)}")
                    if e.response:
                        print(f"Detalhes: {e.response.text}")
                    
            except Exception as e:
                print(f"🔥 Erro crítico: {str(e)}")
                
            finally:
                time.sleep(DELAY_ENTRE_CONTATOS)
        
        print("\n-----------------------------------------")
        print(f"🎉 Disparo concluído! | Sucessos: {enviados_com_sucesso}/{total_contatos}")
        return f"Total de mídias enviadas: {enviados_com_sucesso}"
        
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return f"Erro no disparo: {str(e)}"
    
if __name__ == "__main__":
    resultado = run_envio_PDF(TEXTO_MENSAGEM)
    resultado = run_envio_mensegem()
    resultado = run_envio_midia()
    print(resultado)
