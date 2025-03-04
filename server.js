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
const MEDIA_BASE_PATH = path.join(__dirname, 'assets');
const MEDIA_PATH = assetsDir

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

const ALLOWED_EXTENSIONS = {
    image: ['.jpg', '.jpeg', '.png', '.gif'],
    video: ['.mp4', '.mov', '.avi', '.mkv']
};

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

function validateMediaPath(userPath) {
    const resolvedPath = path.resolve(MEDIA_BASE_PATH, userPath);
    return resolvedPath.startsWith(MEDIA_BASE_PATH) ? resolvedPath : null;
}

function isValidExtension(filePath, type) {
    const ext = path.extname(filePath).toLowerCase();
    return ALLOWED_EXTENSIONS[type].includes(ext);
}

// Endpoints para envio de mídia
function validateMediaPath(userPath) {
    try {
        // Resolve o caminho completo
        const resolvedPath = path.resolve(MEDIA_BASE_PATH, userPath);
        
        // Verifica se o caminho está dentro da pasta base permitida
        if (!resolvedPath.startsWith(MEDIA_BASE_PATH)) {
            console.error(`Tentativa de acesso a caminho não permitido: ${resolvedPath}`);
            return null;
        }
        
        // Verifica se o arquivo existe
        if (!fs.existsSync(resolvedPath)) {
            console.error(`Arquivo não encontrado: ${resolvedPath}`);
            return null;
        }
        
        return resolvedPath;
    } catch (error) {
        console.error(`Erro ao validar caminho: ${error.message}`);
        return null;
    }
}

// Endpoint corrigido
app.post('/send-image', async (req, res) => {
    try {
        const { chatId, filePath, caption } = req.body;

        // Validação do caminho
        const safePath = validateMediaPath(filePath);
        if (!safePath) {
            return res.status(400).json({ 
                error: "Caminho inválido ou arquivo não encontrado",
                details: `Caminho fornecido: ${filePath}`
            });
        }

        // Verificação de tipo de arquivo
        if (!isValidExtension(safePath, 'image')) {
            return res.status(400).json({ 
                error: "Tipo de arquivo não permitido",
                allowed: ALLOWED_EXTENSIONS.image
            });
        }

        // Envio da mídia
        const media = MessageMedia.fromFilePath(safePath);
        await client.sendMessage(chatId, media, { caption });
        
        res.json({ 
            success: true,
            message: "Imagem enviada com sucesso"
        });

    } catch (error) {
        console.error("Erro no send-image:", error);
        res.status(500).json({ 
            error: "Falha no envio da imagem",
            details: error.message
        });
    }
});


const { execSync } = require('child_process'); // Adicione no início do arquivo

// ... (outras importações)

app.post('/send-video', async (req, res) => {
    try {
        const { chatId, filePath, caption } = req.body;
        const safePath = validateMediaPath(filePath);

        // Validação inicial
        if (!safePath) {
            return res.status(400).json({ 
                error: "Caminho inválido",
                details: `Arquivo não encontrado: ${filePath}`
            });
        }

        // Verificação automática do formato
        let media;
        try {
            media = MessageMedia.fromFilePath(safePath);
        } catch (e) {
            console.log('Conversão automática iniciada...');
            const outputPath = `${safePath}.converted.mp4`;
            
            execSync(`ffmpeg -y -i "${safePath}" \
                -c:v libx264 -profile:v baseline \
                -pix_fmt yuv420p \
                -c:a aac \
                -movflags +faststart \
                "${outputPath}"`);
            
            media = MessageMedia.fromFilePath(outputPath);
        }

        // Envio com fallback
        try {
            await client.sendMessage(chatId, media, { caption });
        } catch (error) {
            await client.sendMessage(chatId, media, {
                caption,
                sendMediaAsDocument: true
            });
        }

        res.json({ success: true });

    } catch (error) {
        res.status(500).json({
            error: "Falha no envio",
            userInstructions: [
                "1. Verifique se o arquivo é um vídeo válido",
                "2. Reduza a duração para menos de 1 minuto",
                "3. Se o problema persistir, converta para MP4"
            ],
            technical: error.message
        });
    }
});

app.listen(port, "0.0.0.0" , () => {
    console.log(`Servidor rodando na porta ${port}`);
});