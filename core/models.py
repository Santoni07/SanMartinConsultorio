from django.db import models
from django.contrib.auth.models import User

class CentroMedico(models.Model):

    nombre = models.CharField(max_length=200)

    direccion = models.CharField(max_length=300)

    telefono = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro Médico"
        verbose_name_plural = "Centros Médicos"

    def __str__(self):
        return self.nombre 
class PerfilUsuario(models.Model):

    ROLES = [
        ('ADMIN', 'Administrador'),
        ('RECEPCION', 'Recepción'),
        ('MEDICO', 'Médico'),
    ]
    centros = models.ManyToManyField(
        CentroMedico,
        blank=True
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='RECEPCION'
    )

    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil Usuario"
        verbose_name_plural = "Perfiles Usuarios"

    def __str__(self):
        return f"{self.user.username} - {self.rol}"