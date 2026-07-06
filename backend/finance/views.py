from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.db.models import Q, Sum, Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from utils.permissions import ViewModelPermissions
from rest_framework.response import Response

from typing import cast

from .models import Account, AccountType, Category, Ledger, Transaction, Transfer
from utils.exceptions import BusinessException
from utils.code_enum import CodeEnum
from utils.response import success_response
from .serializers import (
    AccountSerializer,
    AccountTypeSerializer,
    CategorySerializer,
    LedgerSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
    TransferSerializer,
)


class LedgerViewSet(viewsets.ModelViewSet):
    queryset = Ledger.objects.all()
    serializer_class = LedgerSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_queryset(self):
        qs = Ledger.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.time_categories.exists() or instance.category_categories.exists():
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message=f"账本「{instance.name}」下还有分类，请先删除或转移分类后再删除账本",
                http_status=400,
            )
        instance.delete()

    @action(detail=False, methods=["post"], url_path="recalculate")
    def recalculate(self, request):
        from decimal import Decimal
        from django.db.models import Sum

        categories = Category.objects.all()
        ledgers = Ledger.objects.all()
        accounts = Account.objects.all()

        if not request.user.is_superuser:
            categories = categories.filter(
                Q(time_ledger__user=request.user) | Q(category_ledger__user=request.user)
            )
            ledgers = ledgers.filter(user=request.user)
            accounts = accounts.filter(user=request.user)

        cat_count = 0
        for cat in categories:
            total = cat.transactions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            cat.actual_amount = total.quantize(Decimal("0.01"))
            cat.save(update_fields=["actual_amount", "updated_at"])
            cat_count += 1

        ledger_count = 0
        for lg in ledgers:
            lg.recalculate()
            ledger_count += 1

        acc_count = 0
        for acc in accounts:
            acc.recalculate()
            acc_count += 1

        return success_response(data={
            "categories": cat_count,
            "ledgers": ledger_count,
            "accounts": acc_count,
        })


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_queryset(self):
        qs = Account.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        account_type = self.request.query_params.get("account_type")
        if account_type:
            qs = qs.filter(account_type=account_type)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        instance.recalculate()

    def perform_destroy(self, instance):
        if instance.transactions.exists():
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message=f"账户「{instance.name}」下还有交易记录，请先删除或转移交易后再删除账户",
                http_status=400,
            )
        if instance.transfers_out.exists() or instance.transfers_in.exists():
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message=f"账户「{instance.name}」有关联的转账记录，请先删除或转移转账后再删除账户",
                http_status=400,
            )
        instance.delete()


class AccountTypeViewSet(viewsets.ModelViewSet):
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]
    pagination_class = None

    def perform_destroy(self, instance):
        if instance.accounts.exists():
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message=f"账户类型「{instance.name}」下还有账户，请先删除或转移账户后再删除该类型",
                http_status=400,
            )
        instance.delete()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_queryset(self):
        qs = Category.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(
                Q(time_ledger__user=self.request.user)
                | Q(category_ledger__user=self.request.user)
            )
        return qs

    def perform_destroy(self, instance):
        if instance.transactions.exists():
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message=f"分类「{instance.name}」下还有交易记录，请先删除或转移交易后再删除分类",
                http_status=400,
            )
        instance.delete()


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "batch"]:
            return TransactionCreateSerializer
        return TransactionSerializer

    @action(detail=False, methods=["post"], url_path="batch")
    def batch(self, request):
        items = request.data.get("transactions", [])
        if not isinstance(items, list) or not items:
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="请提供 transactions 数组",
                http_status=400,
            )

        results = []
        has_error = False

        for idx, item in enumerate(items):
            serializer = self.get_serializer(data=item)
            if not serializer.is_valid():
                has_error = True
                results.append({
                    "row": idx,
                    "success": False,
                    "errors": serializer.errors,
                })
                continue

            try:
                with db_transaction.atomic():
                    serializer.save()
                results.append({
                    "row": idx,
                    "success": True,
                    "errors": None,
                })
            except Exception as e:
                has_error = True
                results.append({
                    "row": idx,
                    "success": False,
                    "errors": {"_general": [str(e)]},
                })

        return success_response(data={
            "total": len(items),
            "succeeded": sum(1 for r in results if r["success"]),
            "failed": [r for r in results if not r["success"]],
        })

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        qs = self.get_queryset()
        date_from = request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(trade_time__gte=date_from)
        date_to = request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(trade_time__lte=date_to)

        total_income = qs.filter(amount__gt=0).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        total_expense = qs.filter(amount__lt=0).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        def fmt(val):
            return str(val.quantize(Decimal("0.01")))

        net = total_income + total_expense
        total_income = fmt(total_income)
        total_expense = fmt(abs(total_expense))
        net = fmt(net)

        categories = (
            qs.values("category", "category__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("total")
        )

        def fmt_cat(val):
            return str(val.quantize(Decimal("0.01"))) if isinstance(val, Decimal) else str(val)

        recent = qs.order_by("-trade_time", "-created_at")[:10]

        from .serializers import TransactionSerializer

        return Response({
            "total_income": total_income,
            "total_expense": total_expense,
            "net": net,
            "categories": [
                {
                    "id": c["category"],
                    "name": c["category__name"],
                    "total": fmt_cat(c["total"]),
                    "count": c["count"],
                }
                for c in categories
            ],
            "recent_transactions": TransactionSerializer(recent, many=True).data,
        })

    @action(detail=False, methods=["get"], url_path="daily-summary")
    def daily_summary(self, request):
        from datetime import timedelta

        today = date.today()
        date_from = request.query_params.get("date_from", today.replace(day=1).isoformat())
        date_to = request.query_params.get("date_to", today.isoformat())

        qs = self.get_queryset().filter(trade_time__gte=date_from, trade_time__lte=date_to)

        daily = {}
        for d in qs.values("trade_time").annotate(
            income=Sum("amount", filter=Q(amount__gt=0)),
            expense=Sum("amount", filter=Q(amount__lt=0)),
        ):
            daily[d["trade_time"]] = {
                "income": float(d["income"] or 0),
                "expense": float(d["expense"] or 0),
            }

        def fmt_d(n):
            return "{:.2f}".format(abs(n))

        result = []
        start = date.fromisoformat(date_from)
        end = date.fromisoformat(date_to)
        current = start
        while current <= end:
            info = daily.get(current, {"income": 0, "expense": 0})
            result.append({
                "date": current.isoformat(),
                "income": fmt_d(info["income"]),
                "expense": fmt_d(info["expense"]),
            })
            current += timedelta(days=1)

        return Response(result)

    def get_queryset(self):
        queryset = Transaction.objects.all()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(category__time_ledger__user=self.request.user)
                | Q(category__category_ledger__user=self.request.user)
            )
        category_id = self.request.query_params.get("category_id")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        account_id = self.request.query_params.get("account_id")
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        ledger_id = self.request.query_params.get("ledger_id")
        if ledger_id:
            queryset = queryset.filter(
                Q(category__time_ledger=ledger_id) | Q(category__category_ledger=ledger_id)
            )
        partner = self.request.query_params.get("partner")
        if partner:
            queryset = queryset.filter(partner__icontains=partner)
        date_from = self.request.query_params.get("date_from")
        if date_from:
            queryset = queryset.filter(trade_time__gte=date_from)
        date_to = self.request.query_params.get("date_to")
        if date_to:
            queryset = queryset.filter(trade_time__lte=date_to)
        tx_type = self.request.query_params.get("type")
        if tx_type == "income":
            queryset = queryset.filter(amount__gt=0)
        elif tx_type == "expense":
            queryset = queryset.filter(amount__lt=0)
        amount_min = self.request.query_params.get("amount_min")
        if amount_min:
            if tx_type == "expense":
                queryset = queryset.filter(amount__lte=-float(amount_min))
            else:
                queryset = queryset.filter(amount__gte=amount_min)
        amount_max = self.request.query_params.get("amount_max")
        if amount_max:
            if tx_type == "expense":
                queryset = queryset.filter(amount__gte=-float(amount_max))
            else:
                queryset = queryset.filter(amount__lte=amount_max)
        star = self.request.query_params.get("star")
        if star:
            queryset = queryset.filter(star__gte=star)
        return queryset


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_queryset(self):
        qs = Transfer.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        from_account = self.request.query_params.get("from_account")
        if from_account:
            qs = qs.filter(from_account_id=from_account)
        to_account = self.request.query_params.get("to_account")
        if to_account:
            qs = qs.filter(to_account_id=to_account)
        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(trade_time__gte=date_from)
        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(trade_time__lte=date_to)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
