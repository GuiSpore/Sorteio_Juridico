from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import random
from .models import Juiz, Processo

@login_required
def home(request):
    # Se o usuário for um Juiz, redireciona automaticamente para o painel dele
    if hasattr(request.user, 'juiz_profile'):
        return redirect('painel_juiz')

    # Se o usuário for um Assessor, redireciona para o painel dele
    if hasattr(request.user, 'assessor_profile'):
        return redirect('painel_assessor')

    # Restringe o acesso apenas para Assistentes Jurídicos e Administradores (Superusers)
    if not hasattr(request.user, 'assistente_profile') and not request.user.is_superuser:
        return HttpResponseForbidden("<div style='text-align: center; margin-top: 50px; font-family: sans-serif;'><h2>Acesso Negado 🛑</h2><p>Apenas Assistentes Jurídicos podem acessar a página de sorteio de processos.</p></div>")

    # Se o usuário clicou no botão de sortear o processo
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'cadastrar':
            numero = request.POST.get('numero')
            complexidade = request.POST.get('complexidade')
            if numero and complexidade:
                try:
                    Processo.objects.create(
                        numero=numero,
                        complexidade=int(complexidade),
                        status='Aguardando Sorteio'
                    )
                    messages.success(request, f'Processo {numero} cadastrado na fila de sorteio!')
                except IntegrityError:
                    messages.error(request, f"Erro: O processo número {numero} já foi cadastrado.")
                except Exception as e:
                    messages.error(request, f"Ocorreu um erro inesperado: {str(e)}")
                    
        elif acao == 'sortear':
            pendentes = Processo.objects.filter(status='Aguardando Sorteio')
            qtd_sorteados = pendentes.count()
            
            if qtd_sorteados == 0:
                messages.warning(request, "Nenhum processo aguardando sorteio.")
            else:
                # Busca os juízes ativos e calcula o peso somando a complexidade dos processos deles
                juizes_ativos = list(Juiz.objects.filter(ativo=True).annotate(
                    peso_total=Coalesce(Sum('processos__complexidade'), 0)
                ))
                
                if not juizes_ativos:
                    messages.error(request, "Nenhum juiz ativo disponível para sorteio.")
                else:
                    for processo in pendentes:
                        # 1. Encontra a menor pontuação total
                        menor_peso = min(j.peso_total for j in juizes_ativos)
                        # 2. Filtra os juízes empatados
                        juizes_elegiveis = [j for j in juizes_ativos if j.peso_total == menor_peso]
                        # 3. Sorteia e atribui
                        juiz_sorteado = random.choice(juizes_elegiveis)
                        processo.juiz = juiz_sorteado
                        processo.status = 'Sorteado'
                        processo.save()
                        
                        # 4. Atualiza o peso do juiz escolhido na memória para o próximo processo da fila
                        juiz_sorteado.peso_total += processo.complexidade
                        
                    messages.success(request, f"{qtd_sorteados} processos foram sorteados com sucesso!")
                
        return redirect('home')

    # Se for um acesso normal, preparar os dados para o "Placar"
    juizes_status = Juiz.objects.annotate(
        total_basico=Count('processos', filter=Q(processos__complexidade=1)),
        total_medio=Count('processos', filter=Q(processos__complexidade=2)),
        total_avancado=Count('processos', filter=Q(processos__complexidade=3)),
        total_geral=Count('processos'),
        peso_total=Coalesce(Sum('processos__complexidade'), 0)
    ).order_by('nome')

    processos_pendentes = Processo.objects.filter(status='Aguardando Sorteio')

    contexto = {
        'juizes_status': juizes_status, 
        'niveis_complexidade': Processo.NIVEIS_COMPLEXIDADE,
        'processos_pendentes': processos_pendentes
    }
    return render(request, 'sorteio/sorteio.html', contexto)

@login_required
def painel_juiz(request):
    # Verifica se o usuário logado possui um perfil de juiz e não é superuser
    if not hasattr(request.user, 'juiz_profile') and not request.user.is_superuser:
        messages.error(request, "Acesso negado. Apenas juízes podem acessar este painel.")
        return redirect('home')
        
    # Usa getattr para evitar erro (RelatedObjectDoesNotExist) caso seja o superuser sem perfil
    juiz = getattr(request.user, 'juiz_profile', None)
    
    if juiz:
        meus_processos = Processo.objects.filter(juiz=juiz).order_by('-data_cadastro')
        outros_juizes = Juiz.objects.exclude(id=juiz.id)
    else:
        meus_processos = Processo.objects.none()
        outros_juizes = Juiz.objects.all()

    juiz_selecionado_id = request.GET.get('ver_juiz')
    processos_outro_juiz = None
    juiz_selecionado = None
    
    # Se o juiz selecionou outro juiz para visualizar os processos
    if juiz_selecionado_id:
        try:
            juiz_selecionado = Juiz.objects.get(id=juiz_selecionado_id)
            processos_outro_juiz = Processo.objects.filter(juiz=juiz_selecionado).order_by('-data_cadastro')
        except Juiz.DoesNotExist:
            pass

    contexto = {
        'juiz': juiz or {'nome': 'Administrador (Visão Global)'},
        'meus_processos': meus_processos,
        'outros_juizes': outros_juizes,
        'processos_outro_juiz': processos_outro_juiz,
        'juiz_selecionado': juiz_selecionado,
    }
    return render(request, 'sorteio/painel_juiz.html', contexto)

@login_required
def painel_assessor(request):
    # Verifica se o usuário logado possui um perfil de assessor e não é superuser
    if not hasattr(request.user, 'assessor_profile') and not request.user.is_superuser:
        messages.error(request, "Acesso negado. Apenas assessores podem acessar este painel.")
        return redirect('home')
        
    # Usa getattr para evitar erro caso seja o superuser sem perfil
    assessor = getattr(request.user, 'assessor_profile', None)
    
    if assessor:
        juiz = assessor.juiz
        processos = Processo.objects.filter(juiz=juiz).order_by('-data_cadastro')
    else:
        juiz = None
        processos = Processo.objects.all().order_by('-data_cadastro')

    contexto = {
        'assessor': assessor or {'nome': 'Administrador'},
        'juiz': juiz or {'nome': 'Geral (Todos os Processos)'},
        'processos': processos,
    }
    return render(request, 'sorteio/painel_assessor.html', contexto)