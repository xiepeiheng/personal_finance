from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, LedgerViewSet, TransactionViewSet

router = DefaultRouter()
router.register("ledgers", LedgerViewSet)
router.register("categories", CategoryViewSet)
router.register("transactions", TransactionViewSet)

urlpatterns = router.urls
