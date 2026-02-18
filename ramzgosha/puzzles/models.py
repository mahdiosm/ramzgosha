# puzzles/models.py
import re
from django.db import models
from django.contrib.auth.models import User
from django.utils.html import mark_safe


class Puzzle(models.Model):
    date = models.DateField(unique=True, verbose_name="تاریخ انتشار")
    tagged_clue = models.TextField(verbose_name="متن معما با تگ",
                                   help_text="مثال: این {def}تعریف{/def} و این {fod}مصالح{/fod} است.", null=True)

    clue_text = models.TextField(editable=False)

    answer = models.CharField(max_length=50, verbose_name="پاسخ")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="طراح")

    desc_definition = models.TextField(blank=True, verbose_name="توضیح تعریف")
    desc_fodder = models.TextField(blank=True, verbose_name="توضیح مصالح (Fodder)")
    desc_indicators = models.TextField(blank=True, verbose_name="توضیح نشانگرها")

    def save(self, *args, **kwargs):
        if self.tagged_clue:
            clean_text = re.sub(r'\{(def|fod|ind)\}(.*?)\{/\1\}', r'\2', self.tagged_clue)
            clean_text = " ".join(clean_text.split())

            self.clue_text = clean_text

        super().save(*args, **kwargs)

    @property
    def html_render(self):
        if not self.tagged_clue:
            return ""

        text = self.tagged_clue.strip()

        # \s* باعث می‌شود اگر کاربر نوشته باشد {def} کلمه {/def}، آن اسپیس‌های اضافی حذف شوند
        text = re.sub(r'\{def\}\s*(.*?)\s*\{/def\}', r'<span class="hint-span hint-def">\1</span>', text)
        text = re.sub(r'\{fod\}\s*(.*?)\s*\{/fod\}', r'<span class="hint-span hint-fod">\1</span>', text)
        text = re.sub(r'\{ind\}\s*(.*?)\s*\{/ind\}', r'<span class="hint-span hint-ind">\1</span>', text)

        return mark_safe(text)

    @property
    def answer_length(self):
        return len(self.answer.replace(" ", ""))

    def __str__(self):
        return f"{self.date} - {self.clue_text[:20]}..."