const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode-terminal');
const cors = require('cors');
const multer = require('multer');
const fs = require('fs');
const path = require('path');


// Caminho corrigido com criação automática da pasta
const assetsDir = path.join(__dirname, 'assets');
if (!fs.existsSync(assetsDir)) {
    fs.mkdirSync(assetsDir);
}

const PDF_PATH = path.join(assetsDir, 'promocoes.pdf');

// Verificação inicial
if (!fs.existsSync(PDF_PATH)) {
    console.error('ERRO: Arquivo não encontrado!');
    console.error('Solução:');
    console.error('1. Crie a pasta "assets"');
    console.error('2. Coloque o arquivo "promocoes.pdf" dentro dela');
    console.error(`Caminho completo exigido: ${PDF_PATH}`);
    process.exit(1);
}
const app = express();
const port = 3000;

// Configurações iniciais
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors());

// Garante que a pasta de uploads existe
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// Configuração do Multer
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, file.originalname);
    }
});
const upload = multer({ storage });

// Cliente WhatsApp
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', qr => {
    console.log('Escaneie o QR Code para conectar:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('Cliente WhatsApp está pronto!');
});

client.initialize();

// Rotas
app.post('/send-message', async (req, res) => {
    try {
        const { chatId, message } = req.body;
        if (!chatId || !message) {
            return res.status(400).json({ error: 'Parâmetros inválidos' });
        }

        await client.sendMessage(chatId, message);
        res.status(200).json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/send-file', upload.single('file'), async (req, res) => {
    try {
        const { chatId } = req.body;
        if (!chatId || !req.file) {
            return res.status(400).json({ error: 'Parâmetros inválidos' });
        }

        const media = MessageMedia.fromFilePath(req.file.path);
        await client.sendMessage(chatId, media);

        // Limpa o arquivo após o envio
        fs.unlinkSync(req.file.path);
        
        res.status(200).json({ success: true });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/unread-messages', async (req, res) => {
    try {
        const chats = await client.getChats();
        const messages = [];

        for (const chat of chats) {
            if (chat.unreadCount > 0) {
                const unreadMsgs = await chat.fetchMessages({ limit: chat.unreadCount });
                unreadMsgs.forEach(msg => {
                    messages.push({
                        id: msg.id.id,
                        from: msg.from,
                        body: msg.body,
                        timestamp: msg.timestamp,
                        sender: { pushname: msg._data.notifyName || 'Desconhecido' }
                    });
                });
            }
        }

        res.status(200).json(messages);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});


// Adicione este novo endpoint no servidor
app.post('/send-pdf', async (req, res) => {
    try {
        console.log('[DEBUG] Recebida requisição para:', req.body.chatId);
        
        const media = MessageMedia.fromFilePath(PDF_PATH);
        const result = await client.sendMessage(req.body.chatId, media);
        
        console.log('[SUCESSO] PDF enviado para:', req.body.chatId);
        res.status(200).json({ success: true });
        
    } catch (error) {
        console.error('[ERRO CRÍTICO] Falha no envio:', error);
        res.status(500).json({ 
            error: error.message,
            stack: error.stack 
        });
    }
});

// Adicione esta função de verificação aprimorada
// Atualize a rota de verificação
app.get('/check-number', async (req, res) => {
    try {
        const { chatId } = req.query;
        
        // Validação rigorosa
        if (!/^55\d{10,}$/.test(chatId)) {
            return res.status(400).json({
                error: "Formato inválido",
                example: "Use 55DDDNNNNNNNN (ex: 5587988149274)"
            });
        }

        const numeroFormatado = `${chatId}@c.us`;
        
        // Método oficial e confiável
        const result = await client.getNumberId(numeroFormatado);
        
        res.status(200).json({
            registered: !!result,
            whatsappId: result?.user || null,
            debug: result // Para análise
        });
        
    } catch (error) {
        console.error('Erro detalhado:', error);
        res.status(500).json({
            error: "Falha na verificação",
            technicalDetails: error.message,
            stack: error.stack
        });
    }
});

app.listen(port, () => {
    console.log(`Servidor rodando na porta ${port}`);
});