from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def verificar_estoque(nome_produto):
    # Configuração do Chrome WebDriver (usando webdriver_manager para gerenciar o chromedriver)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Para rodar sem abrir a janela do navegador
    
    # Usar webdriver_manager para garantir que o chromedriver esteja sempre atualizado
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # URL da loja
    url = f"https://www.magazineluiza.com.br/busca/{nome_produto.replace(' ', '+')}/"    
    driver.get(url)
    
    # Aguarde o carregamento da página
    driver.implicitly_wait(5)
    
    try:
        # Verifique a disponibilidade do produto (ajuste conforme a estrutura da página)
        produto_disponivel = driver.find_element(By.CLASS_NAME, 'availability')  # Substitua pela classe correta
        if produto_disponivel:
            return "Produto disponível em estoque!"
    except:
        return "Produto fora de estoque."
    
    driver.quit()

# Exemplo de chamada
nome_produto = "iphone 11"
resultado = verificar_estoque(nome_produto)
print(resultado)
