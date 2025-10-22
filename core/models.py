from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class FinancialReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    company_name = models.CharField(max_length=255, blank=True, null=True)
    month = models.CharField(max_length=20, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    business_type = models.CharField(max_length=50, blank=True, null=True) # Jasa, Manufaktur, Dagang
    business_status = models.CharField(max_length=50, blank=True, null=True) # PKP, Non PKP
    umkm_incentive = models.CharField(max_length=10, blank=True, null=True) # Ya, Tidak
    omzet = models.BigIntegerField(default=0)
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
                 raise ValidationError("Product must be selected for 'Pendapatan dari Usaha'.")
            self.total = self.quantity * self.selling_price
            # Copy product name into the 'name' field
            self.name = self.product.name
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

    # Calculated Fields (We'll calculate these in the view or model methods later)
    # total_awal = models.BigIntegerField(default=0) # Qty * Harga
    # total_pembelian_bruto = models.BigIntegerField(default=0) # Qty * Harga
    # jumlah_retur_rp = models.BigIntegerField(default=0) # Retur Qty * Harga
    # total_pembelian_neto = models.BigIntegerField(default=0) # Bruto - Diskon - Retur + Ongkir
    # total_akhir = models.BigIntegerField(default=0) # Complex avg cost formula

    class Meta:
        # Prevent multiple Awal/Akhir entries per product per report
        unique_together = ('report', 'product', 'category')
        ordering = ['product__name', 'category']

    def __str__(self):
        return f"{self.product.name} - {self.get_category_display()}"

# --- ExpenseItem (No change needed for now) ---
class ExpenseItem(models.Model):
    TYPE_CHOICES = [
        ('usaha', 'Beban Usaha Lainnya'), # Renamed slightly for clarity
        ('lain', 'Beban Lain-lain'),
    ]
    report = models.ForeignKey(FinancialReport, on_delete=models.CASCADE, related_name="expense_items")
    expense_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='usaha')
    name = models.CharField(max_length=255)
    total = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.get_expense_type_display()}: {self.name} (Rp {self.total})"