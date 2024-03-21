from django.urls import path
from rest_framework import routers

from .views import BookMVS, BorrowingView, BorrowingDetailView, BasicBookMVS

router = routers.DefaultRouter()
router.register('books', BookMVS)
router.register('kitaplar', BasicBookMVS)

urlpatterns = [
    path('borrowings/', BorrowingView.as_view()),
    path('borrowings/<int:pk>/', BorrowingDetailView.as_view()),
]

urlpatterns += router.urls