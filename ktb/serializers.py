from rest_framework import serializers
from .models import Book, Borrowing
from rest_framework.validators import UniqueTogetherValidator
from django.utils import timezone
from datetime import date


class BasicBookSerializer(serializers.ModelSerializer):

    class Meta:
        model = Book
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField()
    current_borrower = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'author',
            'isbn',
            'book_cover',
            'current_borrower',
            'availability',
            'is_available'
        )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')

        if request.user.is_staff:
            fields.pop('is_available')

        if request.user and not request.user.is_staff:
            fields.pop('availability')
            fields.pop('current_borrower')
        return fields
    
    def get_current_borrower(self, obj):
        today = date.today()
        current_borrowings = obj.books.filter(
            borrow_date__lte = today,
            return_date__gte = today
        )
        
        if current_borrowings.exists():
            return current_borrowings.first().borrower.username
        else:
            return None
    
    


class BorrowingSerializer(serializers.ModelSerializer):

    number_of_days_borrowed = serializers.SerializerMethodField()
    book_name = serializers.SerializerMethodField()
    book_isbn = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = (
            'id',
            'borrower',
            'book',
            'book_name',
            'book_isbn',
            'borrow_date',
            'return_date',
            'number_of_days_borrowed'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Borrowing.objects.all(),
                fields=('borrower', 'book', 'borrow_date', 'return_date'),
                message=('You already have a borrowing on these dates.')
            )
        ]

    def get_number_of_days_borrowed(self, obj):
        return (obj.return_date - obj.borrow_date).days
    
    def get_book_name(self, obj):
        return obj.book.title
    
    def get_book_isbn(self, obj):
        return obj.book.isbn


    def validate(self, data):
        book = data['book']
        borrow_date = data['borrow_date']
        return_date = data['return_date']

        existing_borrowings = Borrowing.objects.filter(
            book=book,
            return_date__gte=borrow_date,
            borrow_date__lte=return_date
        ).exclude(id=self.instance.id if self.instance else None)

        if existing_borrowings.exists():
            raise serializers.ValidationError("The book is not available for borrowing on these dates.")
        return super().validate(data)
    



    
    

class ReturnSerializer(serializers.Serializer):
    scanned_isbn = serializers.CharField(max_length=13)

    def validate_scanned_isbn(self, value):
        try:
            book = Book.objects.get(isbn=value)
            return book
        except Book.DoesNotExist:
            raise serializers.ValidationError("Book with this ISBN not found.")
        
    def validate(self, data):
        borrowed_book = self.context['borrowed_book']
        scanned_book = data['scanned_isbn']

        if borrowed_book.isbn != scanned_book.isbn:
            raise serializers.ValidationError("Scanned ISBN does not match the borrowed book's ISBN.")

        return data

    def save(self, borrowing_instance):
        borrowing_instance.return_date = timezone.now().date()
        borrowing_instance.book.availability = True  # Mark the book as available
        borrowing_instance.book.save()
        borrowing_instance.save()