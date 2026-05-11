from django.db import models
from django.contrib.auth.models import User

class Juiz(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='juiz_profile')
    nome = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True, verbose_name="Status Ativo")

    def __str__(self):
        return self.nome

class Assessor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='assessor_profile')
    juiz = models.OneToOneField(Juiz, on_delete=models.CASCADE, related_name='assessor')
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"Assessor: {self.nome} (Juiz: {self.juiz.nome})"

class AssistenteJuridico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='assistente_profile')
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"Assistente Jurídico: {self.nome}"

class Processo(models.Model):
    NIVEIS_COMPLEXIDADE = [
        (1, 'Básico'),
        (2, 'Intermediário'),
        (3, 'Complexo'),
    ]

    STATUS_CHOICES = [
        ('Aguardando Sorteio', 'Aguardando Sorteio'),
        ('Sorteado', 'Sorteado'),
    ]

    numero = models.CharField(max_length=50, unique=True, verbose_name="Número do Processo")
    complexidade = models.IntegerField(choices=NIVEIS_COMPLEXIDADE)
    juiz = models.ForeignKey(Juiz, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Aguardando Sorteio')
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.numero} - Complexidade: {self.get_complexidade_display()}"
