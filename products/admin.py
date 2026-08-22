# from django.contrib import admin

# from .models import Product


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "name",
#         "tenant",
#         "is_archived",
#         "created_by",
#     )  # Biar gampang dilihat
#     list_filter = ("tenant", "is_archived")  # Biar bisa difilter per tenant

#     # INI KUNCINYA! Ngebuka mata Django Admin
#     def get_queryset(self, request):
#         # Paksa Django Admin pake global_objects, bukan default manager
#         qs = self.model.global_objects.get_queryset()

#         # (Opsional) Kalau lu mau nerapin pencarian/ordering bawaan admin
#         # pastikan query-nya tetep dieksekusi
#         return qs
