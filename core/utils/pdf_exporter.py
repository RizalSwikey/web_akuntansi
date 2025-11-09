import pdfkit
from django.template.loader import render_to_string
from django.conf import settings

def generate_pdf_file(report, data, template_path, request=None):
    
    html = render_to_string(template_path, {
        **data,
        "report": report,
    })

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-right": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "enable-local-file-access": "",
        "quiet": "",  # suppress wkhtmltopdf warnings
    }

    config = None
    if hasattr(settings, "WKHTMLTOPDF_CMD"):
        import os
        config = pdfkit.configuration(wkhtmltopdf=settings.WKHTMLTOPDF_CMD)

    pdf = pdfkit.from_string(html, False, options=options, configuration=config)
    
    return pdf