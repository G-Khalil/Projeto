# 🚀 Guia Rápido: Como Testar Reconhecimento Facial

## ⚡ INÍCIO RÁPIDO (5 minutos)

### 1. Clonar e Configurar
```bash
git clone https://github.com/G-Khalil/controle_obra.git
cd controle_obra
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### 2. Preparar Banco de Dados
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Criar usuário admin
```

### 3. Rodar Servidor
```bash
python manage.py runserver
# Acesse: http://localhost:8000/admin
```

## 📝 Testando a Funcionalidade

### Passo a Passo no Admin:

1. **Login**: Acesse `http://localhost:8000/admin` com suas credenciais

2. **Criar Empresa** (se não houver):
   - Vá em "Empresas" → "Adicionar"
   - Preencha nome e dados
   - Salve

3. **Adicionar Funcionário**:
   - Vá em "Funcionários" → "Adicionar"
   - Nome: Digite seu nome
   - Empresa: Selecione a empresa criada
   - Função: Digite uma função
   - Telefone: Digite um número
   - **NÃO preencha foto ainda**
   - Clique "Salvar"

4. **Capturar Foto com Câmera**:
   - Após salvar, procure pelo botão "Capturar Foto"
   - Permita acesso à câmera
   - Seu rosto aparecerá no vídeo
   - Clique "Capturar Foto"
   - Clique "Salvar Foto"
   - Foto será salva no banco!

5. **Verificar Dados Salvos**:
   - Volte à lista de funcionários
   - Clique no funcionário
   - Verifique se a foto foi salva
   - Campos adicionados:
     - `facial_data`: Dados do reconhecimento (JSON)
     - `facial_registered_at`: Data/hora do registro

## 🔍 Verificar Dados no Banco

```bash
python manage.py shell
```

```python
from funcionarios.models import Funcionario
f = Funcionario.objects.first()
print(f"Nome: {f.nome}")
print(f"Tem Foto: {bool(f.foto)}")
print(f"Dados Faciais: {f.facial_data}")
print(f"Registrado em: {f.facial_registered_at}")
exit()
```

## 🐛 Troubleshooting Rápido

| Problema | Solução |
|----------|----------|
| Câmera não funciona | Verifique permissões do navegador / conexão USB |
| CSRF token inválido | Recarregue a página / Limpe cookies |
| Arquivo não salva | Verifique permissões de `media/funcionarios/` |
| Port 8000 em uso | Use `python manage.py runserver 8001` |

## 📚 Documentação Completa

Veja arquivo: `GUIA_TESTES_RECONHECIMENTO_FACIAL.md` na pasta `funcionarios/templates/funcionarios/`

## ✅ Checklist de Funcionalidades

- ✅ Modelo de dados com campos faciais
- ✅ Template de captura de foto
- ✅ Captura via câmera
- ✅ Salva foto no servidor
- ⏳ Reconhecimento facial com face-api.js (próxima fase)
- ⏳ Validação de rosto em tempo real
- ⏳ Matching de rostos
- ⏳ Check-in automático por facial

## 🎯 Próximos Passos

1. Integrar face-api.js para detecção de faces
2. Capturar embeddings faciais
3. Validar rosto durante registro
4. Implementar matching para check-in/check-out

**Dúvidas?** Verifique o guia completo ou abra uma issue no GitHub! 🚀
