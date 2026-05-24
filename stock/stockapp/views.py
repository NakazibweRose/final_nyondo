from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum,F,ExpressionWrapper,DecimalField
from .models import Stock
from salesapp.models import Sales
from openpyxl import Workbook
from salesapp.models import Product, Sales
from schemeapp.models import SchemeCustomer, SchemePayment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import Group
# from stockapp.decorators import role_required, login_required_custom


# @login_required_custom
def stock_list(request):
    receipts = Stock.objects.all().order_by("-date")
    return render(request, 'stock_list.html', {'receipts': receipts})

# @role_required('Admin', 'Staff')
def create_receipt(request):
    products = Product.objects.all()
    if request.method == 'POST':
        product = get_object_or_404(Product, id=request.POST.get('product'))
        unit_cost = float(request.POST.get('unit_cost') or 0)
        amount_paid = float(request.POST.get('amount_paid') or 0)
        receipt = Stock.objects.create(
            product=product,
            supplier=request.POST.get('supplier'),
            quantity=int(request.POST.get('quantity')),
            unit_cost=unit_cost,
            amount_paid=amount_paid,
            selling_price=float(request.POST.get('price') or 0),
            is_paid=request.POST.get('is_paid') == 'on'
        )

        product.unit_price = unit_cost
        product.selling_price = float(request.POST.get('price') or 0)
        product.save()
        return redirect('goods_received_note', receipt_id=receipt.id)

    # products = Product.objects.all()
    return render(request, 'create_receipt.html', context={'products': products})

# @login_required_custom
def goods_received_note(request, receipt_id):
    receipt = get_object_or_404(Stock, id=receipt_id)

    if receipt.is_paid:
        total_amount_due = 0
    else:
        total_amount_due = (
            receipt.quantity * receipt.unit_cost
        ) - receipt.amount_paid

    return render(request, 'goods_received_note.html', {
        'receipt': receipt,
        'total_amount_due': total_amount_due
    })
# @role_required('Admin', 'Staff')
def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == "POST":
        stock.product = get_object_or_404(Product, id=request.POST.get("product"))
        stock.supplier = request.POST.get("supplier")
        stock.quantity = int(request.POST.get("quantity") or 0)
        stock.unit_price = float(request.POST.get("unit_cost") or 0)
        stock.amount_paid = float(request.POST.get("amount_paid") or 0)
        stock.selling_price = float(request.POST.get("price") or 0)
        stock.is_paid = bool(request.POST.get("is_paid"))

        stock.product.unit_price = stock.unit_cost
        stock.product.selling_price = stock.selling_price
        stock.product.save()

        stock.save()
        return redirect("stock_list")

    return render(request, "stock_edit.html", {
        "stock": stock,
        "products": Product.objects.all()
    })

# @role_required('Admin')
def delete_receipt(request, pk):
    receipt = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        receipt.delete()
        return redirect('stock_list')
    return render(request, 'delete_receipt.html', context={'receipt': receipt})

# @login_required_custom
def stock_report(request):
    products = Product.objects.all()
    report = []
    for product in products:
        total_received = Stock.objects.filter(
            product=product
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(total=Sum('quantity'))['total'] or 0

        current_stock = total_received - total_sold

        if current_stock <= 5:
            status = 'Low Stock'
        elif current_stock <= 20:
            status = 'Medium Stock'
        else:
            status = 'High Stock'

        report.append({
            'product': product,
            'total_received': total_received,
            'total_sold': total_sold,
            'current_stock': current_stock,
            'status': status,
        })

    return render(request, 'stock_report.html', context={'report': report})


# @login_required_custom
def dashboard(request):

    total_sales = Sales.objects.aggregate(total=Sum('total_price'))['total'] or 0
    total_sales_count = Sales.objects.count()


    total_stock_value = Stock.objects.aggregate(total=Sum('unit_cost'))['total'] or 0
    total_products = Product.objects.count()

    
    total_scheme_customers = SchemeCustomer.objects.count()
    total_scheme_payments = SchemePayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0


    sales_by_product = Sales.objects.values('product_name__product_name').annotate(total=Sum('quantity')).order_by('-total')[:7]
    

    low_stock = []
    for product in Product.objects.all():
        total_received = Stock.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0
        total_sold = Sales.objects.filter(product_name=product).aggregate(total=Sum('quantity'))['total'] or 0
        available = total_received - total_sold
        if available <= 10:
            low_stock.append({'product': product.product_name, 'available': available})

    
    recent_sales = Sales.objects.all().order_by('-sale_date')[:5]

    return render(request, 'dashboard.html', {
        'total_sales': total_sales,
        'total_sales_count': total_sales_count,
        'total_stock_value': total_stock_value,
        'total_products': total_products,
        'total_scheme_customers': total_scheme_customers,
        'total_scheme_payments': total_scheme_payments,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
    })


# @role_required('Admin')
# @role_required('Admin')
def user_management(request):
    from django.contrib.auth.models import User
    users = User.objects.all().prefetch_related('groups')
    groups = Group.objects.all()
    return render(request, 'user_management.html', {'users': users, 'groups': groups})


# @role_required('Admin')
def assign_role(request, user_id):
    from django.contrib.auth.models import User
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        group_name = request.POST.get('role')
        user.groups.clear()
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
    return redirect('user_management')


# @role_required('Admin')
def export_stock_report_excel(request):
    products = Product.objects.all()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Stock Report"

    worksheet.append([
        "Product",
        "Category",
        "Total Received",
        "Total Sold",
        "Current Stock",
        "Status"
    ])

    for product in products:
        total_received = Stock.objects.filter(
            product=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        total_sold = Sales.objects.filter(
            product_name=product
        ).aggregate(total=Sum("quantity"))["total"] or 0

        current_stock = total_received - total_sold

        if current_stock <= 5:
            status = "Low Stock"
        elif current_stock <= 20:
            status = "Medium Stock"
        else:
            status = "High Stock"

        worksheet.append([
            product.product_name,
            product.category_name.category_name,
            total_received,
            total_sold,
            current_stock,
            status
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="stock_report.xlsx"'

    workbook.save(response)

    return response

def supplier_report(request):

    suppliers = Stock.objects.values('supplier').annotate(

        total_quantity=Sum('quantity'),

        total_goods_value=Sum(ExpressionWrapper(F('quantity') * F('unit_cost'),output_field=DecimalField()
)
        ),

        total_paid=Sum('amount_paid')

    ).order_by('-total_paid')

    # Calculate amount due
    for supplier in suppliers:
        supplier['amount_due'] = ((supplier['total_goods_value'] or 0)- (supplier['total_paid'] or 0))

    return render(request, 'supplier_report.html', {'suppliers': suppliers})


