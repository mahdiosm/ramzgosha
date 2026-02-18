from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Puzzle

@admin.register(Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('date', 'clue_text', 'answer', 'author')