# Guia de Teste: Reconhecimento Facial - Controle Obra

## 1. Pré-requisitos

### Instalar Dependências do Projeto

```bash
# Clonar o repositório
git clone https://github.com/G-Khalil/controle_obra.git
cd controle_obra

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 2. Configurar Banco de Dados

```bash
# Aplicar migrações
python manage.py makemigrations
python manage.py migrate

# Criar usuário admin
python manage.py createsuperuser
# Insira: username, email, senha
```

## 3. Executar o Servidor Django

```bash
# Rodar servidor local
python manage.py runserver

# Servidor estará em: http://localhost:8000
# Admin em: http://localhost:8000/admin
```

## 4. Acessar a Interface de Teste

### Passo 1: Login no Admin
1. Acesse: `http://localhost:8000/admin`
2. Faça login com usuário criado

### Passo 2: Registrar uma Empresa (se não houver)
1. Clique em "Empresas"
2. Clique em "Adicionar Empresa"
3. Preencha os dados
4. Salve

### Passo 3: Registrar Novo Funcionário
1. Vá para "Funcionarios"
2. Clique em "Adicionar Funcionário"
3. Preencha os campos:
   - Nome: Seu nome
   - Empresa: Selecione a empresa criada
   - Função: Digite sua função
   - Telefone: Digite um número
4. **NÃO preencha a foto ainda**
5. Clique em "Salvar"

### Passo 4: Capturar Foto (Teste Atual)
1. Após salvar, clique em "Capturar Foto"
2. Permita acesso à câmera
3. Seu rosto deve aparecer no vídeo
4. Clique em "Capturar Foto"
5. A imagem será capturada
6. Clique em "Salvar Foto"
7. A foto será salva no banco de dados

## 5. Testar Reconhecimento Facial (Próxima Fase)

### Para ativar reconhecimento facial avançado:

#### Instalar face-api.js
```bash
# Adicionar ao template HTML
<script src="https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.min.js"></script>
```

#### Criar arquivo de configuração
Crie `static/js/facial_recognition.js`:
```javascript
// Carregar modelos de reconhecimento facial
Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
    faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
    faceapi.nets.faceRecognitionNet.loadFromUri('/static/models'),
    faceapi.nets.faceExpressionNet.loadFromUri('/static/models')
]).then(startVideo);

async function detectFaces(video) {
    const detections = await faceapi
        .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks()
        .withFaceDescriptors()
        .withFaceExpressions();
    return detections;
}
```

## 6. Testes de Integração (Bash)

### Teste via cURL
```bash
# Testar captura de foto
curl -X POST http://localhost:8000/admin/funcionarios/funcionario/salvar-foto/ \
  -H "Content-Type: application/json" \
  -d '{
    "funcionario_id": 1,
    "imagem": "data:image/jpeg;base64,..."
  }'
```

### Teste via Python
```python
import requests
import json
from django.test import Client

# Criar cliente de teste
client = Client()

# Login
client.login(username='admin', password='senha')

# Enviar foto
response = client.post('/admin/funcionarios/funcionario/salvar-foto/', 
    data=json.dumps({
        'funcionario_id': 1,
        'imagem': 'data:image/jpeg;base64,...'
    }),
    content_type='application/json'
)

print(response.json())
```

## 7. Verificar Dados Salvos

### Via Admin Django
1. Vá para `http://localhost:8000/admin/funcionarios/funcionario/`
2. Clique no funcionário criado
3. Verifique se os campos foram preenchidos:
   - `foto`: imagem salva
   - `facial_data`: dados JSON do reconhecimento (quando implementado)
   - `facial_registered_at`: data/hora do registro

### Via Banco de Dados
```bash
# Abrir shell Django
python manage.py shell

# Consultar dados
from funcionarios.models import Funcionario
funcionario = Funcionario.objects.first()
print(f"Nome: {funcionario.nome}")
print(f"Tem foto: {bool(funcionario.foto)}")
print(f"Dados faciais: {funcionario.facial_data}")
print(f"Registrado em: {funcionario.facial_registered_at}")
```

## 8. Troubleshooting

### Erro: "Câmera não encontrada"
- Verifique se a câmera está conectada
- Teste em outro navegador
- Verifique permissões do navegador

### Erro: "CSRF Token inválido"
- Recarregue a página
- Limpe cookies do navegador
- Verifique settings.py do Django

### Erro: "Arquivo não salvo"
- Verifique diretório `media/funcionarios/`
- Confirme permissões de escrita
- Verifique espaço em disco

## 9. Próximos Passos

1. ✅ Modelo de dados criado
2. ✅ Template de captura existente
3. ⏳ Integrar face-api.js
4. ⏳ Criar backend para processar reconhecimento
5. ⏳ Testar reconhecimento facial em tempo real
6. ⏳ Salvar embeddings faciais no banco
7. ⏳ Validar rosto durante check-in/check-out

## 10. Recursos Úteis

- [Django Documentation](https://docs.djangoproject.com/)
- [face-api.js GitHub](https://github.com/vladmandic/face-api)
- [TensorFlow.js](https://www.tensorflow.org/js)
- [MDN - getUserMedia API](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)
