# -*- coding: utf-8 -*-
{
    'name': "Divisa",

    'summary': """ Calculadora de divisas """,

    'description': """
         Calculadora de divisas
    """,

    'author': "Jeff S.",
    'website': "http://www.sispavgt.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['product'],

    'data': [
        'data/ir_sequence_data.xml',
        'views/divisa_views.xml',
        'security/ir.model.access.csv',
        'views/reporte_divisa.xml',
        'views/report.xml',

    ],
}
