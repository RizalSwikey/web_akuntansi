# core/utils/excel_exporter.py
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from core.utils.final_report import generate_final_report_data


def generate_excel_file(report):
    data = generate_final_report_data(report)

    wb = Workbook()
    ws = wb.active
    ws.title = "Laporan Laba Rugi"

    # Styling setup
    bold = Font(bold=True)
    center = Alignment(horizontal="center")
    border = Border(top=Side(style="thin"), bottom=Side(style="thin"))
    header_fill = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")

    # ========== HEADER ==========
    ws.append([report.company_name])
    ws.append(["LAPORAN LABA RUGI"])
    ws.append([f"{report.month} {report.year}"])
    ws.append([])

    # ========== PENDAPATAN ==========
    ws.append(["Pendapatan"])
    ws.append(["Jenis", "Jumlah"])
    ws["A6"].font = bold
    ws["B6"].font = bold

    ws.append(["Pendapatan Usaha", data["total_pendapatan_usaha"]])
    ws.append(["Pendapatan Lain-lain", data["total_pendapatan_lain"]])
    ws.append(["Jumlah Pendapatan", data["jumlah_pendapatan"]])
    ws.append([])

    # ========== BEBAN ==========
    ws.append(["Beban"])
    ws.append(["Jenis", "Jumlah"])
    ws["A11"].font = bold
    ws["B11"].font = bold

    ws.append(["HPP", data["total_hpp"]])

    # Beban usaha & lainnya
    for item in data["beban_usaha_items"]:
        ws.append([item.name, item.total])
    ws.append(["Total Beban Usaha", data["total_beban_usaha"]])


    for item in data["beban_lain_items"]:
        ws.append([item.name, item.total])
    ws.append(["Total Beban Lain", data["total_beban_lain"]])


    ws.append(["Jumlah Beban", data["jumlah_beban"]])
    ws.append([])

    # ========== HPP PER PRODUK (Simplified) ==========
    ws.append(["HPP Per Produk"])
    start_row = ws.max_row + 1

    # Header: only show the 3 columns
    ws.append(["Produk", "HPP / Unit", "HPP Total"])

    # Bold Header
    for col in range(1, 4):
        ws.cell(row=start_row + 1, column=col).font = bold

    # Fill data
    for item in data["hpp_per_product"]:
        product_name = item.get("product_name")
        hpp_per_unit = item.get("hpp_per_unit", 0)
        hpp_total = item.get("hpp", 0)

        ws.append([
            product_name,
            hpp_per_unit,
            hpp_total
        ])

        current = ws.max_row
        ws[f"B{current}"].number_format = "#,##0"
        ws[f"C{current}"].number_format = "#,##0"

    ws.append([])  # Empty row after table

    # ========== LABA ==========
    ws.append(["Laba/Rugi Sebelum Pajak Penghasilan", data["laba_sebelum_pajak"]])
    ws.append(["Beban Pajak Penghasilan", data["pajak_penghasilan"]])
    ws.append(["Laba/Rugi Setelah Pajak Penghasilan", data["laba_setelah_pajak"]])
    ws.append([])

    # Auto width
    for col in ws.columns:
        length = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = length + 3

    # Output to bytes
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"Laporan-{report.company_name}-{report.month}-{report.year}.xlsx"
    return buffer.getvalue(), filename
