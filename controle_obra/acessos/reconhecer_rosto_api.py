"""API para reconhecimento facial e registro de entrada/saída.

Este módulo integra a classe FacialRecognitionSystem com Django
para processar fotos via AJAX e retornar o funcionario_id identificado.
"""

import json
import base64
from io import BytesIO
from PIL import Image
import numpy as np

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from acessos.facial_recognition import FacialRecognitionSystem
from funcionarios.models import Funcionario


# Inicializar sistema de reconhecimento facial (singleton)
_facial_system = None


def get_facial_system():
    """Retorna instância do sistema de reconhecimento facial."""
    global _facial_system
    if _facial_system is None:
        _facial_system = FacialRecognitionSystem()
    return _facial_system


@csrf_exempt  # AJAX envia CSRF token no header
@require_http_methods(["POST"])
def reconhecer_rosto(request):
    """
    API endpoint para reconhecer rosto em foto enviada via AJAX.
    
    Espera JSON:
    {
        "foto_base64": "data:image/jpeg;base64,...",
        "tipo": "entrada" ou "saida"
    }
    
    Retorna JSON:
    {
        "sucesso": true/false,
        "funcionario_id": int,
        "nome": str,
        "empresa": str,
        "confianca": float (0-1),
        "mensagem": str
    }
    """
    try:
        data = json.loads(request.body)
        foto_base64 = data.get('foto_base64', '')
        tipo = data.get('tipo', 'entrada')
        
        if not foto_base64:
            return JsonResponse({
                'sucesso': False,
                'erro': 'Nenhuma foto fornecida'
            }, status=400)
        
        # Decodificar base64 para imagem
        try:
            # Remove prefixo "data:image/jpeg;base64," se existir
            if ',' in foto_base64:
                foto_base64 = foto_base64.split(',')[1]
            
            imagem_bytes = base64.b64decode(foto_base64)
            imagem = Image.open(BytesIO(imagem_bytes))
            imagem_array = np.array(imagem)
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro ao decodificar imagem: {str(e)}'
            }, status=400)
        
        # Reconhecer rosto
        sistema_facial = get_facial_system()
        try:
            resultados = sistema_facial.recognize_face(imagem_array)
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro no reconhecimento: {str(e)}'
            }, status=500)
        
        # Processar resultados
        if not resultados:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Nenhum rosto detectado na imagem',
                'tipo': tipo
            })
        
        # Pegar primeiro resultado (confiabilidade mais alta)
        face_locs, nome, funcionario_id, confianca = resultados[0]
        
        if funcionario_id is None:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Rosto não reconhecido - não consta na base de dados',
                'tipo': tipo
            })
        
        if confianca < 0.6:
            return JsonResponse({
                'sucesso': False,
                'erro': f'🚫 Confiança baixa ({confianca:.1%}) - não é possível confirmar identidade',
                'tipo': tipo
            })
        
        # Funcionario identificado com sucesso!
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            empresa = funcionario.empresa.nome if funcionario.empresa else 'N/A'
        except Funcionario.DoesNotExist:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Funcionário {funcionario_id} não encontrado no banco',
                'tipo': tipo
            })
        
        return JsonResponse({
            'sucesso': True,
            'funcionario_id': funcionario_id,
            'nome': nome,
            'empresa': empresa,
            'confianca': round(confianca, 3),
            'tipo': tipo,
            'mensagem': f'✅ Identificado: {nome} ({confianca:.1%} confiança)'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'sucesso': False,
            'erro': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }, status=500)
