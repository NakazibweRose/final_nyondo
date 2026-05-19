from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from .models import Stock
from openpyxl import Workbook
from salesapp.models import Product, Sales

# Stock list
def stock_list(request):
    stocks = Stock.objects.all().order_by("-date")
    stock_data = []
    for stock in stocks:
        total_received = Stock.objects.filter(
            product=stock.product
        ).aggregate(total=Sum('quantity'))['total'] or 0

        total_sold = Sales.objects.filter(
            product_name=stock.product
        ).aggregate(total=Sum('quantity'))['total'] or 0

        available = total_received - total_sold
        stock_data.append({'stock': stock, 'available': available})

    return render(request, 'stock_list.html', {'stock_data': stock_data})

# Create receipt
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

# Goods received note
def goods_received_note(request, receipt_id):
    receipt = get_object_or_404(Stock, id=receipt_id)
    total_amount_due = receipt.quantity * receipt.unit_cost
    return render(request, 'goods_received_note.html', context={'receipt': receipt, 'total_amount_due': total_amount_due})

# Edit receipt
def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)

    if request.method == "POST":
        stock.product = get_object_or_404(Product, id=request.POST.get("product"))
        stock.supplier = request.POST.get("supplier")
        stock.quantity = int(request.POST.get("quantity") or 0)
        stock.unit_cost = float(request.POST.get("unit_cost") or 0)
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

# Delete receipt
def delete_receipt(request, receipt_id):
    receipt = get_object_or_404(Stock, id=receipt_id)
    if request.method == 'POST':
        receipt.delete()
        return redirect('stock_list')
    return render(request, 'delete_receipt.html', context={'receipt': receipt})

# Stock report
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

