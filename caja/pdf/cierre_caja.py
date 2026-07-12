from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generar_pdf_cierre(datos):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=0.6 * cm,
        rightMargin=0.6 * cm,
        topMargin=0.6 * cm,
        bottomMargin=0.6 * cm,
    )

    elementos = []

    styles = getSampleStyleSheet()

    titulo = styles["Heading1"]
    titulo.alignment = TA_CENTER
    subtitulo = styles["Heading2"]
    subtitulo.alignment = TA_CENTER

    normal = styles["BodyText"]
    normal.fontName = "Helvetica"
    normal.fontSize = 8
    normal.leading = 10
    
    pequeno = styles["BodyText"]
    pequeno.fontName = "Helvetica"
    pequeno.fontSize = 7
    pequeno.leading = 8

    elementos.append(
        Paragraph(
            "<b>CENTRO MÉDICO SAN MARTÍN</b>",
            titulo
        )
    )

    elementos.append(
        Paragraph(
            "<b>ACTA DE CIERRE DE CAJA</b>",
            styles["Heading2"]
        )
    )

    elementos.append(
        Spacer(
            1,
            0.30 * cm
        )
    )

    caja = datos["caja"]

    encabezado = [

        [
            "Caja",
            str(caja.id),

            "Sucursal",
            caja.centro_medico.nombre,

            "Fecha",
            caja.fecha.strftime("%d/%m/%Y"),

            "Turno",
            caja.get_turno_display(),
        ],

        [
            "Abrió",
            caja.abierta_por.username if caja.abierta_por else "-",

            "Cerró",
            caja.cerrada_por.username if caja.cerrada_por else "-",

            "Hora Apertura",
            caja.fecha_apertura.strftime("%H:%M"),

            "Hora Cierre",
            caja.fecha_cierre.strftime("%H:%M")
            if caja.fecha_cierre else "-",
        ],

    ]

    tabla = Table(

        encabezado,

        colWidths=[

            2.2 * cm,
            2.4 * cm,

            2.2 * cm,
            5.0 * cm,

            2.2 * cm,
            3.2 * cm,

            2.2 * cm,
            2.8 * cm,

        ]

    )

    tabla.setStyle(

        TableStyle([

            ("GRID", (0, 0), (-1, -1), 0.3, colors.black),

            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),

            ("BACKGROUND", (0, 1), (-1, 1), colors.whitesmoke),

            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),

            ("FONTSIZE", (0, 0), (-1, -1), 8),

            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),

            ("TOPPADDING", (0, 0), (-1, -1), 5),

            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ])

    )

    elementos.append(tabla)

    elementos.append(
        Spacer(
            1,
            0.40 * cm
        )
    )
    
    # ======================================================
    # RESUMEN FINANCIERO
    # ======================================================

    elementos.append(

        Paragraph(

            "<b>RESUMEN FINANCIERO</b>",

            styles["Heading3"]

        )

    )

    resumen = [

        [

            "Bruto",

            "IVA",

            "Neto",

            "Honorarios",

            "Consultorio",

            "Retenciones",

            "Efectivo"

        ],

        [

            f"${datos['total_bruto']:,.2f}",

            f"${datos['total_iva']:,.2f}",

            f"${datos['total_neto']:,.2f}",

            f"${datos['total_medico']:,.2f}",

            f"${datos['total_consultorio']:,.2f}",

            f"${datos['total_retenciones']:,.2f}",

            f"${datos['efectivo_a_rendir']:,.2f}",

        ],

    ]

    tabla_resumen = Table(

        resumen,

        colWidths=[

            3.2 * cm,

            2.8 * cm,

            3.2 * cm,

            3.5 * cm,

            3.5 * cm,

            3.2 * cm,

            3.5 * cm,

        ]

    )

    tabla_resumen.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),0.3,colors.black),

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DDDDDD")),

            ("BACKGROUND",(0,1),(-1,1),colors.whitesmoke),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),

            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("FONTSIZE",(0,0),(-1,-1),8),

            ("BOTTOMPADDING",(0,0),(-1,-1),5),

        ])

    )

    elementos.append(tabla_resumen)

    elementos.append(

        Spacer(

            1,

            0.35 * cm

        )

    )
    
    # ======================================================
    # DETALLE DE MOVIMIENTOS
    # ======================================================

    elementos.append(

        Paragraph(

            "<b>DETALLE DE MOVIMIENTOS</b>",

            styles["Heading3"]

        )

    )

    tabla_movimientos = [

        [

            "Hora",

            "Paciente",

            "Prestaciones",

            "Medios de Pago",

            "Bruto",

        ]

    ]

    for mov in datos["movimientos"]:

        prestaciones = []

        for prestacion in mov["prestaciones"]:

            prestaciones.append(

                f"{prestacion['codigo']} - "
                f"{prestacion['descripcion']}"

            )

        texto_prestaciones = "<br/>".join(
            prestaciones
        )

        medios = []

        for medio in mov["medios"]:

            medios.append(

                f"{medio['medio']} "
                f"$ {medio['importe']:,.2f}"

            )

        texto_medios = "<br/>".join(
            medios
        )

        fila = [

            mov["hora"],

            Paragraph(

                mov["paciente"],

                normal,

            ),

            Paragraph(

                texto_prestaciones,

                normal,

            ),

            Paragraph(

                texto_medios,

                normal,

            ),

            Paragraph(

                f"<b>${mov['bruto']:,.2f}</b>",

                normal,

            ),

        ]

        tabla_movimientos.append(
            fila
        )

    tabla = Table(

        tabla_movimientos,

        repeatRows=1,

        colWidths=[

            2.0 * cm,

            5.0 * cm,

            9.5 * cm,

            6.0 * cm,

            3.0 * cm,

        ],

    )

    tabla.setStyle(

        TableStyle([

            (
                "GRID",
                (0,0),
                (-1,-1),
                0.25,
                colors.grey,
            ),

            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.HexColor("#DDDDDD"),
            ),

            (
                "FONTNAME",
                (0,0),
                (-1,0),
                "Helvetica-Bold",
            ),

            (
                "FONTSIZE",
                (0,0),
                (-1,-1),
                7,
            ),

            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "TOP",
            ),

            (
                "BOTTOMPADDING",
                (0,0),
                (-1,-1),
                4,
            ),

            (
                "TOPPADDING",
                (0,0),
                (-1,-1),
                4,
            ),

            (
                "ALIGN",
                (4,1),
                (4,-1),
                "RIGHT",
            ),

        ])

    )

    elementos.append(
        tabla
    )

    elementos.append(

        Spacer(

            1,

            0.30 * cm,

        )

    )
    
    
    doc.build(elementos)
    
    # ======================================================
    # RESUMEN FINAL
    # ======================================================

    elementos.append(

        Spacer(
            1,
            0.30 * cm,
        )

    )

    elementos.append(

        Paragraph(

            "<b>RESUMEN GENERAL</b>",

            styles["Heading3"]

        )

    )

    tabla_totales = [

        [

            "Movimientos",

            "Prestaciones",

            "Pacientes",

            "Efectivo a Rendir",

        ],

        [

            str(datos["cantidad_movimientos"]),

            str(datos["cantidad_prestaciones"]),

            str(datos["cantidad_pacientes"]),

            f"$ {datos['efectivo_a_rendir']:,.2f}",

        ],

    ]

    tabla = Table(

        tabla_totales,

        colWidths=[

            5 * cm,

            5 * cm,

            5 * cm,

            8 * cm,

        ],

    )

    tabla.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),0.3,colors.black),

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DDDDDD")),

            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("FONTSIZE",(0,0),(-1,-1),8),

            ("BOTTOMPADDING",(0,0),(-1,-1),5),

        ])

    )

    elementos.append(tabla)

    elementos.append(

        Spacer(

            1,

            0.40 * cm,

        )

    )

    # ======================================================
    # CONTROL DE RENDICIÓN
    # ======================================================

    elementos.append(

        Paragraph(

            "<b>CONTROL DE RENDICIÓN</b>",

            styles["Heading3"]

        )

    )

    control = [

        [

            "Medio",

            "Sistema",

            "Contado",

            "Diferencia",

        ]

    ]

    for medio in datos["resumen_medios"]:

        control.append(

            [

                medio["medio_pago__nombre"],

                f"$ {medio['total']:,.2f}",

                "________________",

                "________________",

            ]

        )

    tabla = Table(

        control,

        colWidths=[

            8 * cm,

            5 * cm,

            6 * cm,

            6 * cm,

        ],

    )

    tabla.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),0.3,colors.black),

            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DDDDDD")),

            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

            ("FONTSIZE",(0,0),(-1,-1),8),

            ("ALIGN",(1,1),(-1,-1),"CENTER"),

            ("BOTTOMPADDING",(0,0),(-1,-1),5),

        ])

    )

    elementos.append(tabla)

    elementos.append(

        Spacer(

            1,

            0.50 * cm,

        )

    )

    # ======================================================
    # FIRMAS
    # ======================================================

    firmas = [

        [

            "",

            "",

        ],

        [

            "______________________________",

            "______________________________",

        ],

        [

            "Recepcionista",

            "Administración",

        ],

    ]

    tabla = Table(

        firmas,

        colWidths=[

            13 * cm,

            13 * cm,

        ],

    )

    tabla.setStyle(

        TableStyle([

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("FONTSIZE",(0,0),(-1,-1),8),

        ])

    )

    elementos.append(tabla)

    elementos.append(

        Spacer(

            1,

            0.20 * cm,

        )

    )

    # ======================================================
    # PIE
    # ======================================================

    pie = Paragraph(

        "Documento generado automáticamente por Sistema de Gestión "
        "Consultorio San Martín.",

        pequeno,

    )

    elementos.append(pie)

    pdf = buffer.getvalue()

    buffer.close()

    return pdf