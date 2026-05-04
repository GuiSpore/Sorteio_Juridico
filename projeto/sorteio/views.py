from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
from django.db import IntegrityError
import random
from .models import Juiz, Processo


def home(request):
    # Se o usuário clicou no botão de sortear (enviou o formulário)
    if request.method == 'POST':
        numero = request.POST.get('numero')
        complexidade = request.POST.get('complexidade')

        if numero and complexidade:
            try:
                complexidade = int(complexidade)
                
                # 1. Contar quantos processos DESTA complexidade cada juiz possui
                juizes = Juiz.objects.annotate(
                    qtd_processos=Count('processos', filter=Q(processos__complexidade=complexidade))
                )

                if not juizes.exists():
                    messages.error(request, "Você precisa cadastrar os juízes primeiro!")
                    return redirect('home')

                # 2. Descobrir qual é o menor número de processos dessa complexidade
                menor_qtd = min(j.qtd_processos for j in juizes)

                # 3. Filtrar apenas os juízes que estão "empatados" com essa menor quantidade
                juizes_elegiveis = [j for j in juizes if j.qtd_processos == menor_qtd]

                # 4. Sortear aleatoriamente entre os elegíveis (Desempate)
                juiz_sorteado = random.choice(juizes_elegiveis)

                # 5. Salvar o novo processo no banco de dados já vinculado ao juiz
                Processo.objects.create(
                    numero=numero,
                    complexidade=complexidade,
                    juiz=juiz_sorteado
                )

                # Enviar mensagem de sucesso para a tela
                messages.success(request, f'Sucesso! Processo {numero} foi sorteado para: {juiz_sorteado.nome}')
                
            except IntegrityError:
                messages.error(request, f"Erro: O processo número {numero} já foi cadastrado.")
            except Exception as e:
                messages.error(request, f"Ocorreu um erro inesperado: {str(e)}")
                
        return redirect('home')

    # Se for um acesso normal, preparamos os dados para o "Placar"
    juizes_status = Juiz.objects.annotate(
        total_basico=Count('processos', filter=Q(processos__complexidade=1)),
        total_medio=Count('processos', filter=Q(processos__complexidade=2)),
        total_avancado=Count('processos', filter=Q(processos__complexidade=3)),
        total_geral=Count('processos')
    ).order_by('nome')

    contexto = {'juizes_status': juizes_status, 'niveis_complexidade': Processo.NIVEIS_COMPLEXIDADE}
    return render(request, 'sorteio/sorteio.html', contexto)