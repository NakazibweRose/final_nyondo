from django.shortcuts import render, redirect, get_object_or_404
from salesapp.models import Product, Sales
from .models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from django.db.models import Sum
from stockapp.models import Stock

# Create your views here.

def scheme_customer_list(request):
    customers = SchemeCustomer.objects.all().order_by("-date_registered")
    return render(request, "scheme_customer_list.html", {"customers": customers})


def register_scheme_customer(request):
    if request.method == "POST":
        nin_number = request.POST.get("nin_number")
        if SchemeCustomer.objects.filter(nin_number=nin_number).exists():
            return render(request, "register_scheme_customer.html", {
                "error": "A customer with this NIN number already exists."
            })
        
        if phone_number := request.POST.get("phone_number"):
            if not phone_number.startswith(("0", "+256")):
                return render(request, "register_scheme_customer.html", {
                    "error": "Phone number must start with 0 , +256"
                })
            
        
        SchemeCustomer.objects.create(
            full_name=request.POST.get("full_name"),
            nin_number=request.POST.get("nin_number"),
            phone_number=request.POST.get("phone_number"),
            address=request.POST.get("address"),
            occupation=request.POST.get("occupation"),
            employer_name=request.POST.get("employer_name"),
        )
        return redirect("scheme_customer_list")

    return render(request, "register_scheme_customer.html")


def record_scheme_payment(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    if request.method == "POST":
        payment = SchemePayment.objects.create(
            customer=customer,
            amount_paid=request.POST.get("amount_paid"),
            notes=request.POST.get("notes"),
        )

        return redirect("temporary_receipt", payment_id=payment.id)

    return render(request, "record_scheme_payment.html", {"customer": customer})


def temporary_receipt(request, payment_id):
    payment = get_object_or_404(SchemePayment, id=payment_id)
    return render(request, "temporary_receipt.html", {"payment": payment})


def customer_scheme_detail(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)
    payments = SchemePayment.objects.filter(customer=customer)
    pickups = SchemeGoodsPickup.objects.filter(customer=customer)

    total_paid = sum(payment.amount_paid for payment in payments)
    total_goods_value = sum(
        pickup.quantity_taken * pickup.product.unit_price for pickup in pickups
    )

    balance = total_paid - total_goods_value

    return render(request, "customer_scheme_details.html", {
        "customer": customer,
        "payments": payments,
        "pickups": pickups,
        "total_paid": total_paid,
        "total_goods_value": total_goods_value,
        "balance": balance,
    })


def scheme_goods_pickup(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    products = Product.objects.all()

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))
        quantity = int(request.POST.get("quantity"))

        total_received = Stock.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        available_stock = total_received - total_sold

        if quantity > available_stock:
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products,
                "error": f"Not enough stock. Available stock is {available_stock}."
            })

        total_price = product.unit_price * quantity

        sale = Sales.objects.create(
            product_name=product,
            quantity=quantity,
            total_price=total_price
        )

        SchemeGoodsPickup.objects.create(
            customer=customer,
            product=product,
            quantity_taken=quantity,
            linked_sale=sale
        )

        return redirect("invoice", sale_id=sale.id)

    return render(request, "scheme_goods_pickup.html", {
        "customer": customer,
        "products": products,
    })
