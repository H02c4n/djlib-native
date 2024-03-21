from django.contrib import admin
from .models import Book, Borrowing
# Register your models here.


admin.site.register(Book)
admin.site.register(Borrowing)