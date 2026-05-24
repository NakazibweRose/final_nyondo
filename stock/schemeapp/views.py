from django.shortcuts import render, redirect, get_object_or_404
from salesapp.models import Product, Sales
from .models import SchemeCustomer, SchemePayment, SchemeGoodsPickup
from django.db.models import Sum
from stockapp.models import Stock
from django.contrib import messages
from datetime import datetime
from decimal import Decimal

# from stockapp.decorators import role_required, login_required_custom

# Create your views here.

# @login_required_custom
def scheme_customer_list(request):
    customers = SchemeCustomer.objects.all().order_by("-date_registered")
    return render(request, "scheme_customer_list.html", {"customers": customers})


# @role_required('Admin', 'Staff')
def register_scheme_customer(request):
    if request.method == "POST":
        nin_number = request.POST.get("nin_number").strip()
        if len(nin_number) != 14:
            return render(request, "register_scheme_customer.html", {
                "error": "NIN number must be 14 characters long"
            })
        if not nin_number.startswith(("CF", "CM")):
            return render(request, "register_scheme_customer.html", {
                "error": "NIN number must start with CF or CM"
            })
        if SchemeCustomer.objects.filter(nin_number=nin_number).exists():
            return render(request, "register_scheme_customer.html", {
                "error": "A customer with this NIN number already exists."
            })
        
        phone_number = request.POST.get("phone_number").strip()
        if not phone_number .isdigit() or len(phone_number) != 10:
            return render(request, "register_scheme_customer.html", {
                "error": "Phone number must be 10 digits"
            })
        if not phone_number.startswith(("0", "+256")):
            return render(request, "register_scheme_customer.html", {
                "error": "Phone number must start with 0 or +256"
            })
            
        
        SchemeCustomer.objects.create(
            full_name=request.POST.get("full_name"),
            nin_number=request.POST.get("nin_number"),
            phone_number=request.POST.get("phone_number"),
            address=request.POST.get("address"),
            occupation=request.POST.get("occupation"),
            employer_name=request.POST.get("employer_name"),
        )
        messages.success(request, "Scheme customer registered successfully.")
        return redirect("scheme_customer_list")

    return render(request, "register_scheme_customer.html")


# @role_required('Admin', 'Staff', 'Cashier')
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


# @login_required_custom
def temporary_receipt(request, payment_id):
    payment = get_object_or_404(SchemePayment, id=payment_id)
    return render(request, "temporary_receipt.html", {"payment": payment})


# @login_required_custom
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


# @role_required('Admin', 'Staff', 'Cashier')

def scheme_goods_pickup(request, customer_id):
    customer = get_object_or_404(SchemeCustomer, id=customer_id)

    products = Product.objects.filter(
        category_name__category_name__in=["cement", "Iron sheets", "Iron bars"]
    )

    if request.method == "POST":
        product = get_object_or_404(Product, id=request.POST.get("product"))

        try:
            quantity = int(request.POST.get("quantity"))
        except (TypeError, ValueError):
            messages.error(request, "Invalid quantity")
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products
            })

        if quantity <= 0:
            messages.error(request, "Quantity must be greater than 0")
            return render(request, "scheme_goods_pickup.html", {
                "customer": customer,
                "products": products
            })

        unit_price = Decimal(str(product.unit_price))
        base_total = unit_price * quantity

        distance = Decimal(request.POST.get("distance") or "0")

        if distance <= 10 and base_total >= Decimal("500000"):
            transport_cost = Decimal("0")
            transport_note = "free delivery"
        else:
            transport_cost = Decimal("30000")
            transport_note = "standard delivery"

        total_price = base_total + transport_cost

        sale = Sales.objects.create(
            product_name=product,
            quantity=quantity,
            total_price=total_price,
            transport_cost=transport_cost,
            transport_note=transport_note,
            distance=distance
        )

        SchemeGoodsPickup.objects.create(
            customer=customer,
            product=product,
            quantity_taken=quantity,
            linked_sale=sale
        )

        messages.success(request, "Goods pickup recorded successfully.")
        return redirect("invoice", sale_id=sale.id)

    return render(request, "scheme_goods_pickup.html", {
        "customer": customer,
        "products": products
    })

def scheme_report(request):
    sales = Sales.objects.all()

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

   
    if start_date and end_date:
        sales = sales.filter(sale_date__range=[start_date, end_date])


    total_goods = sum(
        s.product_name.unit_price * s.quantity for s in sales
    )

    total_transport = sales.aggregate(
        total=Sum("transport_cost")
    )["total"] 

    grand_total = total_goods + total_transport

    context = {
        "sales": sales,
        "total_goods": total_goods,
        "total_transport": total_transport,
        "grand_total": grand_total,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "scheme_report.html", context)

def scheme_statement(request, customer_id):

    customer = get_object_or_404(
        SchemeCustomer,
        id = customer_id
    )

    pickups = SchemeGoodsPickup.objects.filter(
        customer=customer
    ).select_related("linked_sale", "product")

    total_goods = 0
    total_transport = 0

    for pickup in pickups:
        sale = pickup.linked_sale

        if sale:
            total_goods += sale.total_price + sale.transport_cost
            total_transport += sale.transport_cost

    grand_total = total_goods + total_transport

    context = {
        "customer": customer,
        "pickups": pickups,
        "total_goods": total_goods,
        "total_transport": total_transport,
        "grand_total": grand_total,
    }

    return render(
        request,
        "scheme_statement.html",
        context
    )