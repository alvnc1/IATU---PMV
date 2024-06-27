// openaiConfig.js

const OpenAI = require('openai');

const openai = new OpenAI({
  apiKey: 'sk-proj-ExsS2pKzIZImsxBw87YHT3BlbkFJXxmfOQjbO86CWTnAwYR6',
  apiKeyPrefix: 'Bearer', // Esto depende de cómo OpenAI requiera la autenticación
  baseUrl: 'https://api.openai.com/v1', // Asegúrate de usar la URL correcta de la API
  timeout: 30000,
  dangerouslyAllowBrowser: true, // Opcional: permite el uso en entornos que imiten un navegador
});

module.exports = openai;
  