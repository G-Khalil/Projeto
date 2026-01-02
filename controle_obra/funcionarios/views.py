from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .models import Funcionario
import base64
from PIL import Image
from io import BytesIO
import json
import os
import tempfile


def capturar_foto_funcionario(request, funcionario_id=None):
    """
    Página para capturar foto da webcam
    """
    funcionario = get_object_or_404(Funcionario, id=funcionario_id)

    context = {
        'funcionario': funcionario,
        'funcionario_id': funcionario.id,
    }
    return render(request, 'funcionarios/capturar_foto.html', context)


@require_http_methods(["POST"])
def salvar_foto_funcionario(request):
    """
    Recebe a imagem em base64, salva no ImageField do Funcionario
    e redireciona de volta para o admin.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        funcionario_id = data.get('funcionario_id')
        imagem_base64 = data.get('imagem')

        if not funcionario_id or not imagem_base64:
            return JsonResponse({
                'sucesso': False,
                'mensagem': 'Dados incompletos para salvar a foto.'
            })

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)

        # imagem_base64 vem no formato "data:image/jpeg;base64,AAAA..."
        if ',' in imagem_base64:
            header, imagem_base64 = imagem_base64.split(',', 1)

        img_bytes = base64.b64decode(imagem_base64)
        img = Image.open(BytesIO(img_bytes)).convert('RGB')

        # cria arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file, format='JPEG')
        temp_file.close()

        # caminho dentro de MEDIA_ROOT/funcionarios/
        from django.core.files import File
        file_name = f'funcionario_{funcionario.id}.jpg'
        with open(temp_file.name, 'rb') as f:
            funcionario.foto.save(file_name, File(f), save=True)

        os.remove(temp_file.name)

        redirect_url = reverse(
            'admin:funcionarios_funcionario_change',
            args=[funcionario.id]
        )

        return JsonResponse({
            'sucesso': True,
            'mensagem': 'Foto salva com sucesso.',
            'redirect_url': redirect_url
        })

    except Exception as e:
        return JsonResponse({
            'sucesso': False,
            'mensagem': f'Erro ao salvar foto: {str(e)}'
        })
