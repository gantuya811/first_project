"""
MERRIGE ERP - Захиалгын Django Admin тохиргоо
OrderStatusHistory нь өөрчлөгдөшгүй (immutable) тул Admin-аас нэмэх, засах,
устгах боломжгүй (зөвхөн харах). Order.status-ийг Admin дээр шууд бичих
боломжгүй (readonly) — учир нь шууд бичвэл 12-төлөвт FSM шалгалт болон
түүхийн бичлэг (OrderStatusHistory) алгасагдана. Төлөв зөвхөн
"Төлөв өөрчлөх" тусгай action-аар, OrderService.transition_status()-ийг
дуудаж, FSM-ийн дагуу шилжинэ.
"""

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from apps.orders.models import GroupedOrder, Order, OrderItem, OrderStatusHistory
from apps.orders.services import TRANSITIONS, OrderService
from apps.shared.exceptions import БизнесАлдаа


class OrderStatusTransitionForm(forms.Form):
    new_status = forms.ChoiceField(label="Шинэ төлөв", choices=())
    reason = forms.CharField(
        label="Шалтгаан", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )

    def __init__(self, *args, allowed_statuses=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_status"].choices = [(s.value, s.label) for s in allowed_statuses]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("variant", "quantity", "unit_price")


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    fields = ("from_status", "to_status", "reason", "created_by", "created_at")
    readonly_fields = ("from_status", "to_status", "reason", "created_by", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "seller", "status", "grouped_order", "created_at")
    list_filter = ("status",)
    search_fields = (
        "order_number",
        "seller__phone_number",
        "seller__first_name",
        "seller__last_name",
    )
    readonly_fields = ("uuid", "order_number", "status", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    change_form_template = "admin/orders/order/change_form.html"

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/transition-status/",
                self.admin_site.admin_view(self.transition_status_view),
                name="orders_order_transition_status",
            ),
        ]
        return custom_urls + super().get_urls()

    def transition_status_view(self, request, object_id):
        order = self.get_object(request, object_id)
        if order is None:
            messages.error(request, "Захиалга олдсонгүй.")
            return redirect("admin:orders_order_changelist")

        allowed = TRANSITIONS.get(order.status, set())
        if not allowed:
            messages.warning(
                request,
                f"'{order.get_status_display()}' төлөвөөс цаашид шилжих боломжгүй.",
            )
            return redirect("admin:orders_order_change", object_id)

        if request.method == "POST":
            form = OrderStatusTransitionForm(request.POST, allowed_statuses=allowed)
            if form.is_valid():
                try:
                    OrderService.transition_status(
                        order,
                        form.cleaned_data["new_status"],
                        request.user,
                        form.cleaned_data["reason"],
                    )
                    messages.success(request, "Захиалгын төлөв амжилттай шинэчлэгдлээ.")
                    return redirect("admin:orders_order_change", object_id)
                except БизнесАлдаа as exc:
                    messages.error(request, str(exc))
        else:
            form = OrderStatusTransitionForm(allowed_statuses=allowed)

        context = {
            **self.admin_site.each_context(request),
            "title": f"{order.order_number} — Төлөв өөрчлөх",
            "order": order,
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/orders/order/transition_status.html", context)


@admin.register(GroupedOrder)
class GroupedOrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "created_at")
    readonly_fields = ("uuid", "order_number", "created_at", "updated_at")


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "created_by", "created_at")
    list_filter = ("to_status",)
    readonly_fields = [f.name for f in OrderStatusHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
