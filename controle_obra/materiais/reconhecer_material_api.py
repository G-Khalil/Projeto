"""API para reconhecimento facial em materiais - emprestimo e consumo.
Integra FacialRecognitionSystem para registros automaticos com rosto.
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
from materiais.models import (
    MaterialDevolucao, EmprestimoMaterial,
    MaterialConsumo, SaidaMaterialConsumo
)
from django.utils import timezone

_facial_system = None

def get_facial_system():
    """Retorna instancia do sistema de reconhecimento facial."""
    global _facial_system
    if _facial_system is None:
        _facial_system = FacialRecognitionSystem()
    return _facial_system

@csrf_exempt
@require_http_methods(["POST"])
def reconhecer_emprestimo_material(request):
    """
    API endpoint para reconhecer rosto e registrar emprestimo de material.
    
    Espera JSON:
    {
        "foto_base64": "data:image/jpeg;base64,...",
        "material_id": int,
        "tipo_operacao": "emprestimo" ou "devolucao"
    }
    
    Retorna JSON com resultado do reconhecimento e registro.
    """
    try:
        data = json.loads(request.body)
        foto_base64 = data.get('foto_base64', '')
        material_id = data.get('material_id')
        tipo_operacao = data.get('tipo_operacao', 'emprestimo')
        
        if not foto_base64 or not material_id:
            return JsonResponse({
                'sucesso': False,
                'erro': 'Foto e material_id sao obrigatorios'
            }, status=400)
        
        # Decodificar base64
        try:
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
        
        if not resultados:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Nenhum rosto detectado'
            })
        
        face_locs, nome, funcionario_id, confianca = resultados[0]
        
        if funcionario_id is None or confianca < 0.6:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Rosto nao reconhecido ou confianca baixa'
            })
        
        # Obter dados do funcionario e material
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            material = MaterialDevolucao.objects.get(id=material_id)
        except (Funcionario.DoesNotExist, MaterialDevolucao.DoesNotExist) as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Funcionario ou material nao encontrado: {str(e)}'
            })
        
        # Registrar emprestimo ou devolucao
        try:
            if tipo_operacao == 'emprestimo':
                if material.status != 'disponivel':
                    return JsonResponse({
                        'sucesso': False,
                        'erro': f'Material indisponivel (status: {material.status})'
                    })
                
                emprestimo = EmprestimoMaterial.objects.create(
                    material=material,
                    funcionario=funcionario,
                    funcionario_responsavel_saida=nome,
                    facial_data_saida=resultados[0],
                    confianca_saida=confianca
                )
                
                material.status = 'emprestado'
                material.save()
                
                return JsonResponse({
                    'sucesso': True,
                    'funcionario': nome,
                    'material': material.nome,
                    'operacao': 'emprestimo',
                    'confianca': round(confianca, 3),
                    'mensagem': f'✅ {nome} emprestou {material.nome}'
                })
            
            elif tipo_operacao == 'devolucao':
                emprestimo = EmprestimoMaterial.objects.filter(
                    material_id=material_id,
                    data_devolucao__isnull=True
                ).first()
                
                if not emprestimo:
                    return JsonResponse({
                        'sucesso': False,
                        'erro': 'Nenhum emprestimo pendente para este material'
                    })
                
                emprestimo.data_devolucao = timezone.now().date()
                emprestimo.hora_devolucao = timezone.now().time()
                emprestimo.funcionario_responsavel_entrada = nome
                emprestimo.facial_data_entrada = resultados[0]
                emprestimo.confianca_entrada = confianca
                emprestimo.condicao_devolucao = 'igual'
                emprestimo.save()
                
                material.status = 'disponivel'
                material.save()
                
                return JsonResponse({
                    'sucesso': True,
                    'funcionario': nome,
                    'material': material.nome,
                    'operacao': 'devolucao',
                    'confianca': round(confianca, 3),
                    'mensagem': f'✅ {nome} devolveu {material.nome}'
                })
        
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro ao registrar operacao: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'sucesso': False,
            'erro': 'JSON invalido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reconhecer_saida_consumo(request):
    """
    API endpoint para reconhecer rosto e registrar saida de material de consumo.
    """
    try:
        data = json.loads(request.body)
        foto_base64 = data.get('foto_base64', '')
        material_id = data.get('material_id')
        quantidade = data.get('quantidade', 1)
        
        if not foto_base64 or not material_id:
            return JsonResponse({
                'sucesso': False,
                'erro': 'Foto e material_id sao obrigatorios'
            }, status=400)
        
        # Decodificar e reconhecer rosto
        try:
            if ',' in foto_base64:
                foto_base64 = foto_base64.split(',')[1]
            imagem_bytes = base64.b64decode(foto_base64)
            imagem = Image.open(BytesIO(imagem_bytes))
            imagem_array = np.array(imagem)
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro ao processar imagem: {str(e)}'
            }, status=400)
        
        sistema_facial = get_facial_system()
        try:
            resultados = sistema_facial.recognize_face(imagem_array)
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro no reconhecimento: {str(e)}'
            }, status=500)
        
        if not resultados:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Nenhum rosto detectado'
            })
        
        face_locs, nome, funcionario_id, confianca = resultados[0]
        
        if funcionario_id is None or confianca < 0.6:
            return JsonResponse({
                'sucesso': False,
                'erro': '🚫 Rosto nao reconhecido'
            })
        
        # Registrar saida de consumo
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
            material = MaterialConsumo.objects.get(id=material_id)
            
            if material.quantidade_estoque < quantidade:
                return JsonResponse({
                    'sucesso': False,
                    'erro': f'Estoque insuficiente ({material.quantidade_estoque} disponivel)'
                })
            
            saida = SaidaMaterialConsumo.objects.create(
                material=material,
                funcionario=funcionario,
                quantidade_saida=quantidade,
                responsavel_saida=nome,
                facial_data=resultados[0],
                confianca=confianca
            )
            
            return JsonResponse({
                'sucesso': True,
                'funcionario': nome,
                'material': material.nome,
                'quantidade': quantidade,
                'unidade': material.unidade,
                'confianca': round(confianca, 3),
                'mensagem': f'✅ {nome} retirou {quantidade} {material.unidade} de {material.nome}'
            })
        
        except (Funcionario.DoesNotExist, MaterialConsumo.DoesNotExist) as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Dados nao encontrados: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'sucesso': False,
                'erro': f'Erro ao registrar saida: {str(e)}'
            }, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'sucesso': False,
            'erro': 'JSON invalido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }, status=500)
