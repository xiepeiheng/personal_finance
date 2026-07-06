from rest_framework import serializers

from .models import Account, AccountType, Category, Ledger, Transaction, Transfer


class LedgerSerializer(serializers.ModelSerializer):
    ledger_type_display = serializers.CharField(
        source="get_ledger_type_display", read_only=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Ledger
        fields = [
            "id",
            "ledger_type",
            "ledger_type_display",
            "name",
            "balance",
            "is_complete",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["balance", "created_at", "updated_at"]


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name", "slug", "sort_order"]


class AccountSerializer(serializers.ModelSerializer):
    account_type_name = serializers.CharField(
        source="account_type.name", read_only=True
    )
    account_type_slug = serializers.CharField(
        source="account_type.slug", read_only=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Account
        fields = [
            "id",
            "account_type",
            "account_type_name",
            "account_type_slug",
            "name",
            "initial_balance",
            "current_balance",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["current_balance", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    time_ledger_name = serializers.CharField(
        source="time_ledger.name", read_only=True, allow_null=True
    )
    category_ledger_name = serializers.CharField(
        source="category_ledger.name", read_only=True, allow_null=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "time_ledger",
            "time_ledger_name",
            "category_ledger",
            "category_ledger_name",
            "budget",
            "actual_amount",
            "is_complete",
            "star",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["actual_amount", "created_at", "updated_at"]

    def _check_ledger_owner(self, ledger, field_name):
        if ledger is None:
            return
        request = self.context.get("request")
        if request and not request.user.is_superuser and ledger.user != request.user:
            raise serializers.ValidationError({field_name: "无权使用该账本"})

    def validate(self, data):
        time_ledger = data.get("time_ledger") or (
            self.instance.time_ledger if self.instance else None
        )
        category_ledger = data.get("category_ledger") or (
            self.instance.category_ledger if self.instance else None
        )
        if not time_ledger and not category_ledger:
            raise serializers.ValidationError("消费计划必须至少关联一个账本")
        self._check_ledger_owner(time_ledger, "time_ledger")
        self._check_ledger_owner(category_ledger, "category_ledger")
        return data


class TransferSerializer(serializers.ModelSerializer):
    from_account_name = serializers.CharField(
        source="from_account.name", read_only=True
    )
    to_account_name = serializers.CharField(
        source="to_account.name", read_only=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "id",
            "from_account",
            "from_account_name",
            "to_account",
            "to_account_name",
            "amount",
            "trade_time",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("转账金额必须大于零")
        return value

    def validate(self, data):
        from_account = data.get("from_account") or (
            self.instance.from_account if self.instance else None
        )
        to_account = data.get("to_account") or (
            self.instance.to_account if self.instance else None
        )
        if from_account and to_account and from_account == to_account:
            raise serializers.ValidationError("转账的源账户和目标账户不能相同")
        return data


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(
        source="account.name", read_only=True, allow_null=True
    )
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "category",
            "account",
            "account_name",
            "trade_time",
            "partner",
            "amount",
            "star",
            "channel",
            "detail",
            "ticket_file",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError("金额不能为零")
        return value


class TransactionCreateSerializer(TransactionSerializer):
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        required=True,
    )

    def validate_amount(self, value):
        if value == 0:
            raise serializers.ValidationError("金额不能为零")
        return value

    def validate_category(self, value):
        request = self.context.get("request")
        if request and not request.user.is_superuser:
            owner = value.time_ledger.user if value.time_ledger else value.category_ledger.user
            if owner != request.user:
                raise serializers.ValidationError("无权使用该分类")
        return value
