from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class FinancialReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    company_name = models.CharField(max_length=255, blank=True, null=True)
    month = models.CharField(max_length=20, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True) # Jasa, Manufaktur, Dagang
    business_status = models.CharField(max_length=50, blank=True, null=True) # PKP, Non PKP (orang_pribadi, badan_usaha)
    umkm_incentive = models.CharField(max_length=10, blank=True, null=True) # Ya, Tidak
    omzet = models.BigIntegerField(default=0)
    
    # --- ADDED: Field for handling PTKP Status from profile.html ---
    ptkp_status = models.CharField(max_length=10, blank=True, null=True) 
    # -----------------------------------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Note: persediaan_awal and persediaan_akhir are now handled per product in HppEntry

    def __str__(self):
        return f"{self.company_name} - {self.month} {self.year} ({self.user.username})"

# --- NEW Product Model ---
class Product(models.Model):
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)

    class Meta:
        # Ensure product names are unique within a single report
        unique_together = ('report', 'name')
        ordering = ['name'] # Keep products alphabetically ordered

    def __str__(self):
        return self.name

# --- MODIFIED RevenueItem Model ---
class RevenueItem(models.Model):
    TYPE_CHOICES = [
        ('usaha', 'Pendapatan dari Usaha'),
        ('lain', 'Pendapatan Lain-lain'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="revenue_items")
    revenue_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='usaha')

    # Link to Product for 'usaha' type
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="revenue_entries", null=True, blank=True)

    # Renamed description back to 'name' for consistency
    # This field holds product name for 'usaha' (auto-set) or description for 'lain'
    name = models.CharField(max_length=255, blank=True, null=True, help_text="Product name (for 'usaha') or description (for 'lain')")

    quantity = models.IntegerField(default=1) # Only relevant for 'usaha'
    selling_price = models.BigIntegerField(default=0) # Only relevant for 'usaha'
    total = models.BigIntegerField(default=0) # Main value for 'lain', calculated for 'usaha'

    def save(self, *args, **kwargs):
        if self.revenue_type == 'usaha':
            if not self.product:
                 # Ensure a product object is related before saving revenue item
                 # This validation may be better handled in the view logic for cleaner UX
                 pass 
            self.total = self.quantity * self.selling_price
            # Copy product name into the 'name' field
            self.name = self.product.name if self.product else self.name # Handle potential missing product name if validation fails elsewhere
        else:
            self.product = None # Ensure no product link for 'lain'
            # For 'lain', total is entered directly, name is also entered directly
        super().save(*args, **kwargs)

    def __str__(self):
        if self.revenue_type == 'usaha':
            # Use product name if available, otherwise fallback to name field
            display_name = self.product.name if self.product else self.name
            return f"Pendapatan Usaha: {display_name} (Rp {self.total})"
        else:
            # Use the 'name' field which holds the description for 'lain'
            return f"Pendapatan Lain: {self.name} (Rp {self.total})"

# --- NEW HppEntry Model ---
class HppEntry(models.Model):
    CATEGORY_CHOICES = [
        ('AWAL', 'Persediaan Awal Bahan Baku'),
        ('PEMBELIAN', 'Pembelian Bahan Baku'),
        ('AKHIR', 'Persediaan Akhir Bahan Baku'), # Assuming Bahan Baku for Dagang
        # We can add TENAGA_KERJA, OVERHEAD later if needed for Manufaktur
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_entries")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_entries")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)

    # Common Fields
    quantity = models.IntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)
    harga_satuan = models.BigIntegerField(default=0) # For AWAL, PEMBELIAN

    # Pembelian-Specific Fields
    diskon = models.BigIntegerField(default=0)
    retur_qty = models.IntegerField(default=0)
    ongkir = models.BigIntegerField(default=0)

    class Meta:
        # Prevent multiple Awal/Akhir entries per product per report
        unique_together = ('report', 'product', 'category')
        ordering = ['product__name', 'category']

    def __str__(self):
        return f"{self.product.name} - {self.get_category_display()}"
# ---------------------------
# HPP Manufaktur Models
# ---------------------------
class HppManufactureMaterial(models.Model):
    TYPE_CHOICES = [
        ('BB_AWAL', 'Persediaan Bahan Baku Awal'),
        ('BB_AKHIR', 'Persediaan Bahan Baku Akhir'),
        ('BB_PEMBELIAN', 'Pembelian Bahan Baku'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_materials")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_manufaktur_materials")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    nama_bahan_baku = models.CharField(max_length=255, blank=True, null=True)
    keterangan = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    harga_satuan = models.BigIntegerField(default=0)
    diskon = models.IntegerField(default=0)
    retur_qty = models.IntegerField(default=0)
    retur_amount = models.IntegerField(default=0)  # auto later
    ongkir = models.IntegerField(default=0)
    total = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['product__name', 'type']

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.harga_satuan
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.get_type_display()}"
    

class HppManufactureWIP(models.Model):  # Barang Dalam Proses
    TYPE_CHOICES = [
        ('WIP_AWAL', 'WIP Awal'),
        ('WIP_AKHIR', 'WIP Akhir'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_wip")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_manufaktur_wip")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)
    harga_satuan = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    class Meta:
        ordering = ['product__name', 'type']

    def __str__(self):
        return f"{self.product.name} - {self.get_type_display()} (Rp {self.total})"


class HppManufactureLabor(models.Model):  # BTKL
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_labor")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_manufaktur_labor")

    jenis_tenaga_kerja = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    harga_satuan = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - BTKL (Rp {self.total})"


class HppManufactureOverhead(models.Model):  # BOP
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    nama_biaya = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    harga_satuan = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - BOP (Rp {self.total})"

class HppManufactureProduction(models.Model):  # Barang Diproduksi
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_production")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_manufaktur_production")

    qty_diproduksi = models.IntegerField(default=0)
    total_produksi = models.BigIntegerField(default=0)
    hpp_per_unit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        unique_together = ('report', 'product')
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product.name} - Barang Diproduksi ({self.qty_diproduksi} unit, Rp {self.hpp_per_unit}/unit)"


class HppManufactureFinishedGoods(models.Model):  # Barang Jadi
    TYPE_CHOICES = [
        ('FG_AWAL', 'Persediaan Barang Jadi Awal'),
        ('FG_AKHIR', 'Persediaan Barang Jadi Akhir'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_fg")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_manufaktur_fg")

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.IntegerField(default=0)
    harga_satuan = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['product__name', 'type']

    def __str__(self):
        return f"{self.product.name} - {self.get_type_display()} (Rp {self.total})"

# --- ExpenseItem (No change needed for now) ---
class ExpenseItem(models.Model):
    EXPENSE_CATEGORY_CHOICES = [
        ('usaha', 'Beban Usaha Lainnya'), # Renamed slightly for clarity
        ('lain', 'Beban Lain-lain'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="expense_items")
    expense_category = models.CharField(
        max_length=20,
        choices=EXPENSE_CATEGORY_CHOICES,
        default='usaha'
    )
    expense_type = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    total = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.expense_category}: {self.name} (Rp {self.total})"
