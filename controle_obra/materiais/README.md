# Sistema de Controle de Materiais com Reconhecimento Facial

## Visao Geral

Este modulo implementa um sistema completo de controle de materiais da obra com **reconhecimento facial automatico**.

A dor que resolve:
- Material de devolucao (ferramentas) pode sumir ou quebrar
- Precisa rastrear quem pegou, quando pegou e quando devolveu
- Controle total com historico completo
- Duas categorias diferentes: material de devolucao vs material de consumo

## Arquitetura

### Modelos (models.py)

#### Material de Devolucao (Ferramentas)
- Martelo, Furadeira, Serra, Makita, etc
- Status: disponivel, emprestado, danificado, perdido
- Rastreamento completo de emprestimos e devolucoes

#### Material de Consumo (Insumos)
- Pregos, Madeira, Arames, Parafusos, etc
- Controle de estoque automatico
- Saida registrada com reconhecimento facial

### API com Reconhecimento Facial

Dois endpoints principais:

1. **POST /api/materiais/api/reconhecer-emprestimo/**
   - Reconhece rosto e registra emprestimo OU devolucao
   - Valida confianca de reconhecimento (minimo 60%)
   - Atualiza status do material automaticamente

2. **POST /api/materiais/api/reconhecer-consumo/**
   - Reconhece rosto e registra saida de material de consumo
   - Valida estoque disponivel
   - Atualiza estoque automaticamente

### Integracoes

- **FacialRecognitionSystem**: Reutiliza o mesmo sistema de reconhecimento do app acessos
- **JSONField**: Armazena dados brutos de reconhecimento para auditoria
- **FloatField (confianca)**: Rastreia confianca do reconhecimento

## Fluxo de Dados

### Material de Devolucao
```
Funcionario cara -> API /api/reconhecer-emprestimo/ -> FacialRecognitionSystem
-> Retorna funcionario_id e confianca
-> Cria EmprestimoMaterial com facial_data_saida
-> Muda status do material para 'emprestado'

Devolucao:
Funcionario cara -> API /api/reconhecer-emprestimo/
-> Reconhece funcionario
-> Busca emprestimo pendente
-> Atualiza com facial_data_entrada e condicao_devolucao
-> Muda status de volta para 'disponivel'
```

### Material de Consumo
```
Funcionario cara -> API /api/reconhecer-consumo/
-> FacialRecognitionSystem reconhece rosto
-> Cria SaidaMaterialConsumo com facial_data
-> Atualiza quantidade_estoque automaticamente
```

## Campos de Reconhecimento Facial

### EmprestimoMaterial
- `facial_data_saida`: JSON com dados do rosto na saida
- `confianca_saida`: Float (0-1) confianca na saida
- `facial_data_entrada`: JSON com dados do rosto na devolucao
- `confianca_entrada`: Float (0-1) confianca na entrada

### SaidaMaterialConsumo
- `facial_data`: JSON com dados do rosto
- `confianca`: Float (0-1) confianca do reconhecimento

## Instalacao

1. Adicione 'materiais' em INSTALLED_APPS no settings.py
2. Execute migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Inclua URLs no projeto principal:
   ```python
   path('materiais/', include('materiais.urls'))
   ```

## Uso da API

### Emprestimo
```json
POST /api/materiais/api/reconhecer-emprestimo/
{
    "foto_base64": "data:image/jpeg;base64,...",
    "material_id": 1,
    "tipo_operacao": "emprestimo"
}

Resposta sucesso:
{
    "sucesso": true,
    "funcionario": "Joao Silva",
    "material": "Martelo",
    "operacao": "emprestimo",
    "confianca": 0.95,
    "mensagem": "✅ Joao Silva emprestou Martelo"
}
```

### Saida de Consumo
```json
POST /api/materiais/api/reconhecer-consumo/
{
    "foto_base64": "data:image/jpeg;base64,...",
    "material_id": 5,
    "quantidade": 10
}

Resposta sucesso:
{
    "sucesso": true,
    "funcionario": "Maria Santos",
    "material": "Pregos",
    "quantidade": 10,
    "unidade": "kg",
    "confianca": 0.92,
    "mensagem": "✅ Maria Santos retirou 10 kg de Pregos"
}
```

## Admin Django

Todos os modelos ja estao registrados no admin. Voce pode:
- Gerenciar materiais e estoques
- Ver historico completo de emprestimos
- Consultar dados de reconhecimento facial
- Filtrar por confianca e datas

## Seguranca

- APIs usam `@csrf_exempt` para chamadas AJAX
- Validacoes de confianca minima (60%)
- Auditoria completa com facial_data e confianca
- Rastreamento de quem pegou e quem devolveu

## Proximos Passos

1. Criar views web para interface visual
2. Criar templates com captura de webcam
3. Integrar com interface de kiosque/touchscreen
4. Relatorios de materiais perdidos
5. Alertas de estoque minimo
