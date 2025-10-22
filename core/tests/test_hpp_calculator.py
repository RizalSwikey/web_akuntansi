from django.contrib.auth.models import User
from django.test import TestCase
from types import SimpleNamespace
from core.models import FinancialReport, Product, HppEntry
from core.utils.hpp_calculator import calculate_hpp_for_product


class HppCalculatorTest(TestCase):
    def setUp(self):
        # --- Create user and report ---
        self.user = User.objects.create_user(username="tester", password="test123")
        self.report = FinancialReport.objects.create(
            user=self.user,
            company_name="Dummy Report",
            month="January",
            year=2025
        )

        # --- Create products linked to that report ---
        self.product_a = Product.objects.create(report=self.report, name="a")
        self.product_b = Product.objects.create(report=self.report, name="b")

        # AWAL
        HppEntry.objects.create(
            report=self.report,
            product=self.product_a,
            category="AWAL",
            quantity=100,
            harga_satuan=5000
        )
        HppEntry.objects.create(
            report=self.report,
            product=self.product_b,
            category="AWAL",
            quantity=300,
            harga_satuan=7000
        )

        # PEMBELIAN
        HppEntry.objects.create(
            report=self.report,
            product=self.product_a,
            category="PEMBELIAN",
            quantity=400, harga_satuan=6000,
            diskon=200000, retur_qty=50, ongkir=300000
        )
        HppEntry.objects.create(
            report=self.report,
            product=self.product_b,
            category="PEMBELIAN",
            quantity=700, harga_satuan=8500,
            diskon=400000, retur_qty=50, ongkir=400000
        )

        # AKHIR
        HppEntry.objects.create(
            report=self.report,
            product=self.product_a,
            category="AKHIR",
            quantity=400
        )
        HppEntry.objects.create(
            report=self.report,
            product=self.product_b,
            category="AKHIR",
            quantity=1000
        )

    def make_entry(self, **kwargs):
        """Helper to create fake HppEntry-like objects"""
        defaults = {
            "quantity": 0,
            "harga_satuan": 0,
            "diskon": 0,
            "retur_qty": 0,
            "ongkir": 0,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_excel_case_product_a(self):
        """Matches Excel example for Product A"""
        awal = self.make_entry(quantity=100, harga_satuan=5000)
        pembelian = [
            self.make_entry(quantity=400, harga_satuan=6000, diskon=200000, retur_qty=50, ongkir=300000),
        ]
        akhir = self.make_entry(quantity=400)

        entries = {"AWAL": awal, "PEMBELIAN": pembelian, "AKHIR": akhir}
        result = calculate_hpp_for_product(self.product_a, entries)

        self.assertEqual(result["total_awal"], 500000)
        self.assertEqual(result["total_pembelian_neto"], 2200000)
        self.assertEqual(result["barang_tersedia"], 2700000)
        self.assertEqual(result["total_akhir"], 2150000)
        self.assertEqual(result["hpp"], 550000)

    def test_excel_case_product_b(self):
        """Matches Excel example for Product B"""
        awal = self.make_entry(quantity=300, harga_satuan=7000)
        pembelian = [
            self.make_entry(quantity=700, harga_satuan=8500, diskon=400000, retur_qty=50, ongkir=400000),
        ]
        akhir = self.make_entry(quantity=1000)

        entries = {"AWAL": awal, "PEMBELIAN": pembelian, "AKHIR": akhir}
        result = calculate_hpp_for_product(self.product_b, entries)

        self.assertEqual(result["total_awal"], 2100000)
        self.assertEqual(result["total_pembelian_neto"], 5525000)
        self.assertEqual(result["barang_tersedia"], 7625000)
        self.assertEqual(result["total_akhir"], 7625000)
        self.assertEqual(result["hpp"], 0)


# --- Detailed Diagnostic Test (prints every step for debugging) ---
class HppCalculatorDetailedTest(TestCase):
    """Diagnostic test comparing every Excel step"""

    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import FinancialReport, Product

        self.user = User.objects.create(username="testuser")
        self.report = FinancialReport.objects.create(
            user=self.user, company_name="Dummy Co", month="01", year=2025
        )

        # Create products
        self.product_a = Product.objects.create(report=self.report, name="a")
        self.product_b = Product.objects.create(report=self.report, name="b")

        # AWAL
        HppEntry.objects.create(report=self.report, product=self.product_a, category="AWAL", quantity=100, harga_satuan=5000)
        HppEntry.objects.create(report=self.report, product=self.product_b, category="AWAL", quantity=300, harga_satuan=7000)

        # PEMBELIAN
        HppEntry.objects.create(
            report=self.report, product=self.product_a, category="PEMBELIAN",
            quantity=400, harga_satuan=6000, diskon=200000, retur_qty=50, ongkir=300000
        )
        HppEntry.objects.create(
            report=self.report, product=self.product_b, category="PEMBELIAN",
            quantity=700, harga_satuan=8500, diskon=400000, retur_qty=50, ongkir=400000
        )

        # AKHIR (as per Excel)
        HppEntry.objects.create(report=self.report, product=self.product_a, category="AKHIR", quantity=400)
        HppEntry.objects.create(report=self.report, product=self.product_b, category="AKHIR", quantity=1000)

    def check_product(self, product_name, expected):
        product = {"a": self.product_a, "b": self.product_b}[product_name]

        entries = {
            "AWAL": HppEntry.objects.get(product=product, category="AWAL"),
            "PEMBELIAN": list(HppEntry.objects.filter(product=product, category="PEMBELIAN")),
            "AKHIR": HppEntry.objects.get(product=product, category="AKHIR"),
        }

        result = calculate_hpp_for_product(product, entries)

        p = entries["PEMBELIAN"][0]
        pembelian_bruto = p.quantity * p.harga_satuan
        jumlah_retur_rp = p.retur_qty * p.harga_satuan
        total_pembelian_excel = pembelian_bruto - p.diskon - jumlah_retur_rp + p.ongkir

        print(f"\n=== Product {product_name.upper()} ===")
        print(f"Bruto: {pembelian_bruto:,.0f}")
        print(f"Diskon: {p.diskon:,.0f}")
        print(f"Retur Rp: {jumlah_retur_rp:,.0f}")
        print(f"Ongkir: {p.ongkir:,.0f}")
        print(f"→ Total Pembelian (Excel): {total_pembelian_excel:,.0f}")
        print(f"→ Total Pembelian (Code): {result['total_pembelian_neto']:,.0f}")
        print(f"→ Total Akhir (Excel): {expected['total_akhir']:,.0f}")
        print(f"→ Total Akhir (Code): {result['total_akhir']:,.0f}")
        print(f"→ HPP (Excel expected): {expected['hpp']:,.0f}")
        print(f"→ HPP (Code result): {result['hpp']:,.0f}")
        print("=" * 60)

        self.assertEqual(result["total_awal"], expected["total_awal"])
        self.assertEqual(result["total_pembelian_neto"], expected["total_pembelian_neto"])
        self.assertEqual(result["total_akhir"], expected["total_akhir"])
        self.assertEqual(result["hpp"], expected["hpp"])

    def test_detailed_comparison(self):
        self.check_product("a", {
            "total_awal": 500000,
            "total_pembelian_neto": 2200000,
            "total_akhir": 2150000,
            "hpp": 550000,
        })
        self.check_product("b", {
            "total_awal": 2100000,
            "total_pembelian_neto": 5525000,
            "total_akhir": 7625000,
            "hpp": 0,
        })
