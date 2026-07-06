from rest_framework.routers import DefaultRouter

from .views import AccountTypeViewSet, AccountViewSet, CategoryViewSet, LedgerViewSet, TransactionViewSet, TransferViewSet

router = DefaultRouter()
router.register("ledgers", LedgerViewSet)
router.register("categories", CategoryViewSet)
router.register("transactions", TransactionViewSet)
router.register("accounts", AccountViewSet)
router.register("transfers", TransferViewSet)
router.register("account-types", AccountTypeViewSet)

urlpatterns = router.urls
