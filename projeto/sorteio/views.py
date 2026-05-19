from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
import random
from .models import Magistrado, Processo

@login_required
def home(request):
    # Se o usuário for um Magistrado, redireciona automaticamente para o painel dele
    if hasattr(request.user, 'magistrado_profile'):
        return redirect('painel_magistrado')

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
                # Busca os magistrados ativos e calcula o peso somando a complexidade dos processos deles
                magistrados_ativos = list(Magistrado.objects.filter(ativo=True).annotate(
                    peso_total=Coalesce(Sum('processos__complexidade'), 0)
                ))
                
                if not magistrados_ativos:
                    messages.error(request, "Nenhum magistrado ativo disponível para sorteio.")
                else:
                    for processo in pendentes:
                        # 1. Encontra a menor pontuação total
                        menor_peso = min(m.peso_total for m in magistrados_ativos)
                        # 2. Filtra os magistrados empatados
                        magistrados_elegiveis = [m for m in magistrados_ativos if m.peso_total == menor_peso]
                        # 3. Sorteia e atribui
                        magistrado_sorteado = random.choice(magistrados_elegiveis)
                        processo.magistrado = magistrado_sorteado
                        processo.status = 'Sorteado'
                        processo.save()
                        
                        # 4. Atualiza o peso do magistrado escolhido na memória para o próximo processo da fila
                        magistrado_sorteado.peso_total += processo.complexidade
                        
                    messages.success(request, f"{qtd_sorteados} processos foram sorteados com sucesso!")
                
        return redirect('home')

    # Se for um acesso normal, preparar os dados para o "Placar"
    magistrados_status = Magistrado.objects.annotate(
        total_basico=Count('processos', filter=Q(processos__complexidade=1)),
        total_medio=Count('processos', filter=Q(processos__complexidade=2)),
        total_avancado=Count('processos', filter=Q(processos__complexidade=3)),
        total_geral=Count('processos'),
        peso_total=Coalesce(Sum('processos__complexidade'), 0)
    ).order_by('nome')

    processos_pendentes = Processo.objects.filter(status='Aguardando Sorteio')

    contexto = {
        'magistrados_status': magistrados_status, 
        'niveis_complexidade': Processo.NIVEIS_COMPLEXIDADE,
        'processos_pendentes': processos_pendentes
    }
    return render(request, 'sorteio/sorteio.html', contexto)

@login_required
def painel_magistrado(request):
    # Verifica se o usuário logado possui um perfil de magistrado e não é superuser
    if not hasattr(request.user, 'magistrado_profile') and not request.user.is_superuser:
        messages.error(request, "Acesso negado. Apenas magistrados podem acessar este painel.")
        return redirect('home')
        
    # Usa getattr para evitar erro (RelatedObjectDoesNotExist) caso seja o superuser sem perfil
    magistrado = getattr(request.user, 'magistrado_profile', None)
    
    if magistrado:
        meus_processos = Processo.objects.filter(magistrado=magistrado).order_by('-data_cadastro')
        outros_magistrados = Magistrado.objects.exclude(id=magistrado.id)
    else:
        meus_processos = Processo.objects.none()
        outros_magistrados = Magistrado.objects.all()

    magistrado_selecionado_id = request.GET.get('ver_magistrado')
    processos_outro_magistrado = None
    magistrado_selecionado = None
    
    # Se o magistrado selecionou outro magistrado para visualizar os processos
    if magistrado_selecionado_id:
        try:
            magistrado_selecionado = Magistrado.objects.get(id=magistrado_selecionado_id)
            processos_outro_magistrado = Processo.objects.filter(magistrado=magistrado_selecionado).order_by('-data_cadastro')
        except Magistrado.DoesNotExist:
            pass

    contexto = {
        'magistrado': magistrado or {'nome': 'Administrador (Visão Global)'},
        'meus_processos': meus_processos,
        'outros_magistrados': outros_magistrados,
        'processos_outro_magistrado': processos_outro_magistrado,
        'magistrado_selecionado': magistrado_selecionado,
    }
    return render(request, 'sorteio/painel_magistrado.html', contexto)

@login_required
def painel_assessor(request):
    # Verifica se o usuário logado possui um perfil de assessor e não é superuser
    if not hasattr(request.user, 'assessor_profile') and not request.user.is_superuser:
        messages.error(request, "Acesso negado. Apenas assessores podem acessar este painel.")
        return redirect('home')
        
    # Usa getattr para evitar erro caso seja o superuser sem perfil
    assessor = getattr(request.user, 'assessor_profile', None)
    
    if assessor:
        magistrado = assessor.magistrado
        processos = Processo.objects.filter(magistrado=magistrado).order_by('-data_cadastro')
    else:
        magistrado = None
        processos = Processo.objects.all().order_by('-data_cadastro')

    contexto = {
        'assessor': assessor or {'nome': 'Administrador'},
        'magistrado': magistrado or {'nome': 'Geral (Todos os Processos)'},
        'processos': processos,
    }
    return render(request, 'sorteio/painel_assessor.html', contexto)