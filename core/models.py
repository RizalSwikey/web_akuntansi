from django.db import models
from django.contrib.auth.models import User
class FinancialReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    company_name = models.CharField(max_length=255, blank=True, null=True)
    month = models.CharField(max_length=20, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True)
    business_status = models.CharField(max_length=50, blank=True, null=True)
    umkm_incentive = models.CharField(max_length=10, blank=True, null=True)
    omzet_status = models.CharField(
        max_length=10,
        choices=[('iya', 'Iya'), ('tidak', 'Tidak')],
        blank=True,
        null=True,
        help_text="Apakah omzet lebih dari 500 juta?"
    )

    ptkp_status = models.CharField(max_length=10, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.month} {self.year} ({self.user.username})"


class Product(models.Model):
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('report', 'name')
        ordering = ['name'] 

    def __str__(self):
        return self.name

class RevenueItem(models.Model):
    TYPE_CHOICES = [
        ('usaha', 'Pendapatan dari Usaha'),
        ('lain', 'Pendapatan Lain-lain'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="revenue_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="revenue_entries", null=True, blank=True)

    revenue_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='usaha')
    name = models.CharField(max_length=255, blank=True, null=True, help_text="Product name (for 'usaha') or description (for 'lain')")
    quantity = models.IntegerField(default=1) 
    selling_price = models.BigIntegerField(default=0) 
    total = models.BigIntegerField(default=0) 

    def save(self, *args, **kwargs):
        if self.revenue_type == 'usaha':
            if not self.product:
                 pass 
            self.total = self.quantity * self.selling_price
            self.name = self.product.name if self.product else self.name
        super().save(*args, **kwargs)

    def __str__(self):
        if self.revenue_type == 'usaha':
            display_name = self.product.name if self.product else self.name
            return f"Pendapatan Usaha: {display_name} (Rp {self.total})"
        else:
            return f"Pendapatan Lain: {self.name} (Rp {self.total})"

# HppEntry Model
class HppEntry(models.Model):
    CATEGORY_CHOICES = [
        ('AWAL', 'Persediaan Awal Bahan Baku'),
        ('PEMBELIAN', 'Pembelian Bahan Baku'),
        ('AKHIR', 'Persediaan Akhir Bahan Baku'), 
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_entries")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="hpp_entries")

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    quantity = models.IntegerField(default=0)
    keterangan = models.CharField(max_length=255, blank=True, null=True)
    harga_satuan = models.BigIntegerField(default=0) # For AWAL, PEMBELIAN
    diskon = models.BigIntegerField(default=0)
    retur_qty = models.IntegerField(default=0)
    ongkir = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ('report', 'product', 'category')
        ordering = ['product__name', 'category']

    def __str__(self):
        return f"{self.product.name} - {self.get_category_display()}"
    
# HPP Manufaktur Models
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
    retur_amount = models.IntegerField(default=0)
    ongkir = models.IntegerField(default=0)
    total = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['product__name', 'type']

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
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="hpp_manufaktur_overhead")
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
    status = models.CharField(max_length=255, blank=True, null=True)
    keterangan = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['product__name', 'type']

    def __str__(self):
        return f"{self.product.name} - {self.get_type_display()} (Rp {self.total})"

# ExpenseItem
class ExpenseItem(models.Model):
    EXPENSE_CATEGORY_CHOICES = [
        ('usaha', 'Beban Usaha Lainnya'),
        ('lain', 'Beban Lain-lain'),
    ]
    BUSINESS_SCOPE_CHOICES = [
        ('dagang', 'Dagang'),
        ('manufaktur', 'Manufaktur'),
    ]

    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="expense_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    expense_category = models.CharField(max_length=20, choices=EXPENSE_CATEGORY_CHOICES, default='usaha')
    scope = models.CharField(max_length=20, choices=BUSINESS_SCOPE_CHOICES, default='dagang')
    expense_type = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=255)
    total = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.get_expense_category_display()} - {self.name}"

