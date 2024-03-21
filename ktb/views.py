from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.validators import ValidationError

from .models import Book, Borrowing
from .serializers import BookSerializer, BorrowingSerializer, ReturnSerializer, BasicBookSerializer

from django.db.models import Q, Exists, OuterRef
from django.utils import timezone

import os


class BasicBookMVS(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BasicBookSerializer




class BookMVS(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if self.request.user.is_staff:

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({'message':'Only the administrator has permission to add books.'})
    


    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = super().get_queryset()
        else:
            queryset = super().get_queryset().filter(availability=True)
        borrowing_date = self.request.query_params.get('borrowing_date')
        returning_date = self.request.query_params.get('returning_date')
        title = self.request.query_params.get('title')

        if borrowing_date or returning_date or title:
            queryset = queryset.filter(
                Q(title__icontains=title) if title else Q(),
                Q(availability=True),
            )

            if borrowing_date or returning_date:
                queryset = queryset.annotate(
                    is_available=~Exists(Borrowing.objects.filter(
                        Q(book=OuterRef('pk')) & Q(
                            borrow_date__lt=returning_date
                        ) & Q(
                            return_date__gt=borrowing_date
                        )
                    ))
                )

        return queryset

        # if borrowing_date is not None or returning_date is not None:
        #     queryset = queryset.annotate(
        #         is_available =~Exists(Borrowing.objects.filter(
        #             Q(book=OuterRef('pk')) & Q(
        #                 borrow_date__lt= returning_date
        #             ) & Q(
        #                 return_date__gt=borrowing_date
        #             )
        #         ))
        #     )
        # return queryset

    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        image_path = instance.book_cover.path

        if os.path.exists(image_path):
            os.remove(image_path)
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)
    


class BorrowingView(ListCreateAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)


    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(borrower=self.request.user)
    


class BorrowingDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        return_date = serializer.validated_data.get('return_date')
        book = serializer.validated_data.get('book')
        borrow_date = instance.borrow_date
        today = timezone.now().date()

        if Borrowing.objects.filter(book=book).exists():
            for borrowing in Borrowing.objects.filter(book=book, return_date__gte=today):
                if borrowing.borrow_date and borrow_date and borrowing.borrow_date < borrow_date < return_date:
                    return Response({'message': 'Book is not available'})

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        borrowed_book = instance.book
        return_serializer = ReturnSerializer(data={'scanned_isbn': request.data.get('scanned_isbn')}, context={'borrowed_book': borrowed_book})
        return_serializer.is_valid(raise_exception=True)

        return_serializer.save(instance)

        return Response({'message': 'Book returned successfully.'})
