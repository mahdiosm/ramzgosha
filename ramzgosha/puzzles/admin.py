from django.contrib import admin

# Register your models here.
from import_export.admin import ImportExportModelAdmin # اینو ایمپورت کن
from .models import Puzzle

@admin.register(Puzzle)
class PuzzleAdmin(ImportExportModelAdmin):
    list_display = ('answer', 'author', 'is_verified', 'publish_date', 'date')
    list_filter = ('is_verified', 'author')
    list_editable = ('is_verified', 'publish_date')