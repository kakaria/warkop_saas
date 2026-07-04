from rest_framework.test import APITestCase
from rest_framework import status
from tenants.models import Tenant, TenantMembership
from users.models import User
from orders.models import Order

class DataIsolationTestCase(APITestCase):
    
    def setUp(self):
        """
        1. PERSIAPAN DATA (The Setup)
        Fungsi ini dieksekusi otomatis oleh Django SEBELUM test dimulai.
        Ini adalah tempat kita membuat 'Dummy Data'.
        """
        # --- Bikin Tenant (Warkop) ---
        self.tenant_a = Tenant.objects.create(name="Warkop Kemang", address="Kemang")
        self.tenant_b = Tenant.objects.create(name="Warkop Depok", address="Depok")

        # --- Bikin User & Hak Akses (Kasir A) ---
        self.kasir_a = User.objects.create_user(email="kasir@kemang.com", password="password123")
        TenantMembership.objects.create(
            tenant=self.tenant_a,
            user=self.kasir_a,
            role=TenantMembership.Role.CASHIER
        )

        # --- Bikin Data Transaksi ---
        # PERHATIAN ARSITEK: Kita pakai 'global_objects' (pintu belakang) di sini!
        # Kenapa? Karena saat file test ini jalan, Middleware kita belum menyala.
        # Kalau kita pakai 'objects.create', Custom Manager kita bakal ngeblokir karena
        # Loker Gym (Thread-Local) masih kosong.
        self.order_a = Order.global_objects.create(tenant=self.tenant_a, total_price=50000)
        self.order_b = Order.global_objects.create(tenant=self.tenant_b, total_price=30000)

        # Asumsi endpoint API lu ada di URL ini
        self.url = '/api/orders/'


    def test_tenant_a_cannot_see_tenant_b_orders(self):
        """
        2 & 3. EKSEKUSI SIMULASI & VALIDASI (The Action & Assertions)
        Fungsi ini adalah tempat pelatuk ditarik.
        """
        # Simulasikan Kasir Kemang sedang Login
        self.client.force_authenticate(user=self.kasir_a)

        # 2. THE ACTION: Tembak API-nya!
        # Trik Django: Custom header 'X-Tenant-ID' wajib ditambahin awalan 'HTTP_' 
        # dan underscore oleh Django saat testing.
        response = self.client.get(
            self.url,
            HTTP_X_TENANT_ID=str(self.tenant_a.id)
        )

        # 3. THE ASSERTIONS: Validasi Mutlak (Pembuktian)
        
        # Pastikan server membalas dengan status 200 OK (Tidak error/crash)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ambil data balasan dari server (bentuk JSON)
        data = response.json()

        # VALIDASI 1: Kasir Kemang HARUSNYA cuma nerima 1 data transaksi
        self.assertEqual(len(data), 1, "Gagal: Kasir Kemang harusnya cuma lihat 1 pesanan!")

        # VALIDASI 2: Data yang diterima HARUS milik Order A
        self.assertEqual(data[0]['id'], self.order_a.id, "Gagal: Data yang muncul bukan punya Kemang!")

        # VALIDASI 3 (Data Leak Check): ID Order B SAMA SEKALI TIDAK BOLEH ADA di data response
        order_ids_in_response = [item['id'] for item in data]
        self.assertNotIn(self.order_b.id, order_ids_in_response, "BENCANA: Data Warkop Depok Bocor!")