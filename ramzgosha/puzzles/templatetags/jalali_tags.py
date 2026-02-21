from django import template
import jdatetime

register = template.Library()

MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']

@register.filter
def to_jalali(date_obj):
    if not date_obj:
        return ""
    # تبدیل تاریخ میلادی دیتابیس به شمسی
    jdate = jdatetime.date.fromgregorian(date=date_obj)
    month_name = MONTHS[jdate.month - 1]
    return f"{jdate.day} {month_name} {jdate.year}"