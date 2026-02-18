from django.contrib import admin

# Register your models here.
from import_export.admin import ImportExportModelAdmin # اینو ایمپورت کن
from .models import Puzzle

@admin.register(Puzzle)
class PuzzleAdmin(ImportExportModelAdmin):
    list_display = ('date', 'clue_text', 'answer', 'author')