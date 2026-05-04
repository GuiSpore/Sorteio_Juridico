from django.db import models

class Juiz(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Processo(models.Model):
    NIVEIS_COMPLEXIDADE = [
        (1, 'Básico'),
        (2, 'Médio'),
        (3, 'Avançado'),
    ]

    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Processo")
    complexidade = models.IntegerField(choices=NIVEIS_COMPLEXIDADE)
    juiz = models.ForeignKey(Juiz, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos')
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero} - Complexidade: {self.get_complexidade_display()}"
