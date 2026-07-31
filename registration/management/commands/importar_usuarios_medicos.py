from openpyxl import load_workbook

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from medicos.models import Medico


class Command(BaseCommand):

    help = "Importa usuarios de médicos desde un archivo Excel"

    def add_arguments(self, parser):

        parser.add_argument(
            "archivo",
            type=str,
            help="Ruta del archivo Excel"
        )

    def handle(self, *args, **options):

        archivo = options["archivo"]

        workbook = load_workbook(archivo)

        hoja = workbook.active

        creados = 0
        existentes = 0
        errores = 0

        # ===========================================
        # EL EXCEL
        #
        # A = Nombre
        # B = Matrícula
        # C = Clave
        # D = Usuario
        #
        # La fila 1 son encabezados
        # ===========================================

        for fila in hoja.iter_rows(min_row=2, values_only=True):

            # Saltar filas totalmente vacías
            if not any(fila):
                continue

            nombre = str(fila[0]).strip() if fila[0] else ""
            matricula = str(fila[1]).strip() if fila[1] else ""
            clave = str(fila[2]).strip() if fila[2] else ""
            usuario = str(fila[3]).strip() if fila[3] else ""

            # Validaciones
            if not matricula:
                self.stdout.write(
                    self.style.ERROR(
                        f"{nombre}: matrícula vacía."
                    )
                )
                errores += 1
                continue

            if not usuario:
                self.stdout.write(
                    self.style.ERROR(
                        f"{nombre}: usuario vacío."
                    )
                )
                errores += 1
                continue

            if not clave:
                self.stdout.write(
                    self.style.ERROR(
                        f"{nombre}: clave vacía."
                    )
                )
                errores += 1
                continue

            # Buscar médico
            try:

                medico = Medico.objects.get(
                    matricula=matricula
                )

            except Medico.DoesNotExist:

                self.stdout.write(
                    self.style.ERROR(
                        f"No existe un médico con matrícula {matricula}"
                    )
                )

                errores += 1
                continue

            # ¿Ya tiene usuario?
            if medico.user:

                self.stdout.write(
                    self.style.WARNING(
                        f"{medico.nombre} {medico.apellido} ya tiene usuario."
                    )
                )

                existentes += 1
                continue

            # ¿Ya existe el username?
            if User.objects.filter(username=usuario).exists():

                self.stdout.write(
                    self.style.WARNING(
                        f"El usuario '{usuario}' ya existe."
                    )
                )

                existentes += 1
                continue

            # Crear usuario
            user = User.objects.create_user(

                username=usuario,
                password=clave,
                first_name=medico.nombre,
                last_name=medico.apellido,
                email=medico.email

            )

            # Asociar médico
            medico.user = user
            medico.save()

            creados += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✔ {medico.nombre} {medico.apellido}"
                )
            )

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuarios creados : {creados}"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"Ya existentes    : {existentes}"
            )
        )
        self.stdout.write(
            self.style.ERROR(
                f"Errores          : {errores}"
            )
        )
        self.stdout.write("=" * 60)