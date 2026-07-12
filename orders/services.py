"""
1. bikin order dulu (buat record baru di table Order, ya klo mau buat struk bikin dulu notanya)
2. kalo udah buat order, ambil data dari serializer (yang dari frontend) yang isinya di dalem items
3. ambil product sama quantity
4. karena ini bisa race condition (dua orang beli di waktu yang hampir samaan), jadi pake row lock
5. kalo udah di kunci cek, stock product kalo udah kosong / kurang dari request panggil error, kalo oke lanjut
6. kurangin stok yang ada di database sama quantity
7. save database() buat nyimpen sisa stok
8. bikin total_harga (dari semua harga product * quantity)
10. masukin ke table DetailOrder
9. save ke database()
10. pastiin pake transaction.atomic biar make sifat all or nothing
"""

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.models import Product

from .models import Order, OrderDetail


def process_checkout(tenant_id, user, items_data):
    """
    service layer murni logic bisnis, gak kenal HTTP, serializer, atau middleware
    fokus ngurus uang, dan logika bisnis
    """

    with transaction.atomic():
        # 1 bikin Order dulu
        order = Order.objects.create(
            tenant_id=tenant_id,  # pake ini biar sekali doang ke database
            created_by=user,
            status=Order.Status.PAID,
            total_price=0,
        )

        grand_total = 0

        # 2. ambil data dari DetailOrder
        for item in items_data:
            # karena item dari serializer, 'product' itu isinya object
            product_obj = item["product"]  # nah ini object
            quantity = item["quantity"]

            # 3. lock row si product
            locked_product = Product.objects.select_for_update().get(id=product_obj.id)

            # 4. cek stoknya
            if locked_product.stock < quantity:
                raise ValidationError(
                    f"Stock dari product {locked_product.name} tidak cukup bro! "
                )

            # kurangin stoknya
            locked_product.stock -= quantity
            locked_product.save(
                update_fields=["stock"]
            )  # biar cepet karena yang update cuma field stock

            # hitung total harga dan masukin ke grand_total (total yang harus dibayar)
            total_harga = locked_product.price * quantity
            grand_total += total_harga

            # masukin ke OrderDetail (bikin row baru), btw kalo .create() udah pasti manggil .save()
            OrderDetail.objects.create(
                order=order,
                product=locked_product,  # pake object product (karena kalo butuh item lain, udah ada di RAM, dan gak bakal double query)
                quantity=quantity,
                price_at_transaction=locked_product.price,
                product_name_at_transaction=locked_product.name,
            )

        order.total_price = grand_total
        order.save(update_fields=["total_price"])

        return order


"""
    ganti state machine (Order.Status)
    aturan:
    cuma bisa ganti status yang PAID menjadi VOID
    kalo bukan PAID, tendang aja
    kalo udah VOID, tendang juga

    1. pake transaction.atomic (all or nothing)
    2. ambil order (struknya) pake order_id [PAKE ROW LOCK JUGA]
    3. cek apakah ordernya ada
    4. kalo ada, cek statusnya. kalo PAID lanjut
    5. cek juga kalo statusnya VOID, tendang aja
    6. kalo ada, ambil DetailOrder pake related_name melalui object order (jadi order.items.all()) :items = related_name
    7. looping buat cek setiap product yang dibeli
    8. ambil product pake product_id yang ada di DetailOrder [JANGAN LUPA DI ROW LOCK]
    9. cek product ada gak, kalo gak ada ya lewatin aja
    10. kalo ada balikin stock
    11. save perubahan stock (pake update_fields=['stock']) biar optimize
    12. keluar dari looping terus ganti statusnya jadi VOID
    13. save perubahan status pake update_fields


"""

def void_order_service(tenant_id, order_id):
    """
        SERVICE UNTUK NGELAYANIN PEMBATALAN STRUK (VOID)
        BUAT JALANIN GANTI STATE PAID -> VOID
        DAN JUGA BALIKIN STOCK
        YANG BISA CUMA MANAGER / OWNER
    """

    with transaction.atomic():

        try:
            order = Order.objects.select_for_update().get(
                id=order_id
            )
        except Order.DoesNotExist:
            raise ValidationError(
                f'Struk dengan id{order_id} gak ada cuy!'
            )

        if order.status == Order.Status.VOID: # cegah double click (spam/impontedancy)
            raise ValidationError('Maaf bro, struk ini udah pernah di-VOID')

        if order.status != Order.Status.PAID: # cegah kalo ada status lain
            raise ValidationError('Wah kamu belum bayar ya kwkwk!')

        order_items = order.items.all()


        for item in order_items:
            try:
                # ambil product
                product = Product.objects.select_for_update().get(
                    id = item.product_id
                )

                # ambil stock dari product
                product.stock += item.quantity
                product.save(update_fields=['stock'])

            except Product.DoesNotExist:
                continue # ya skip aja, karena kalo barang gak ada ya yaudah

        order.status = Order.Status.VOID
        order.save(update_fields=['status'])

        return order




