from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True)
    availability = models.BooleanField(default=True)
    book_cover = models.ImageField(upload_to="covers", blank=True, null=True)

    def __str__(self):
        return f"{self.title} -- {self.isbn}"


class Borrowing(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='books')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowers')
    borrow_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"This {self.book.title} is borrowed by {self.borrower.username} from {self.borrow_date} until {self.return_date}."
    
    class Meta:
        unique_together = ['borrower', 'book', 'borrow_date', 'return_date']
    

    