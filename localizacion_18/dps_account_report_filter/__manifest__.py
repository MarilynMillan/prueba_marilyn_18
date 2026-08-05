{
    "name": "Odoo Financial Reports: Currency Filter | Account Report in Multiple Currencies | Account Reports Multi Currency (Original)",
    "summary": "Add multi-currency support to financial reports for accurate global financial analysis. Simplify your financial reporting across multiple currencies with our Multi-Currency Accounting Report module. Tailored for businesses handling international transactions, this app delivers accurate, real-time insights into your accounting data across various currencies.",
    "version": "18.0.6.5.4",
    "category": "Accounting",
    'author': 'Dotsprime System',
    'sequence': 1,
    'email': 'Darrell Sojo',
    'support': 'dsojo.tanfe@gmail.com',
    "website":'dsojo.tanfe@gmail.com',
    "license": 'OPL-1',
    'price': 150,
    'currency': 'USD',
    "description": """
        Potencie a su equipo de contabilidad con informes financieros mejorados al habilitar la compatibilidad con múltiples divisas en estados financieros clave como Balance General, Pérdidas y Ganancias, Estado de Flujo de Caja, Resumen Ejecutivo, Declaración de Impuestos, Libro Mayor, Saldo de Seguimiento, Auditoría del Diario, Registro de Cheques, Libro Mayor de Socios, Cuentas por Cobrar y Cuentas por Pagar.

Este módulo se integra perfectamente con los informes contables de Odoo para permitir cambiar entre la moneda base de la empresa y una moneda alternativa seleccionada, mejorando la visibilidad para operaciones internacionales y auditorías financieras.

Informes Financieros de Odoo: Filtro de Divisas :

            Balance general
            Estado de pérdidas y ganancias
            Estado de flujo de efectivo
            Resumen ejecutivo
            Declaración de impuestos
            Libro mayor
            Saldo de seguimiento
            Auditoría del diario
            Registro de cheques
            Libro mayor de socios
            Cuentas por cobrar vencidas
            Cuentas por pagar vencidas

            Características principales:
            - Añadir filtros de selección de moneda a los informes financieros
            - Ver informes en monedas alternativas para obtener una mejor perspectiva
            - Mejorar la toma de decisiones para empresas con transacciones multidivisa
    """,
    "depends": [
        "account_reports",
    ],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "dps_account_report_filter/static/src/components/**/*",
        ],
    },
    'images': ['static/description/main_screenshot.png'],
    "live_test_url" : "https://youtu.be/2CzQSQYa33g",
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

