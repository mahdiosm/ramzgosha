from django.shortcuts import render

# Create your views here.
# puzzles/views.py
import random
from django.http import JsonResponse
from django.utils import formats
import calendar
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Puzzle
from django.db.models import Max
from datetime import timedelta
from django.contrib.auth.decorators import login_required

def home(request):
    today = timezone.localdate()

    # گرفتن معمای امروز
    try:
        todays_puzzle = Puzzle.objects.get(publish_date=today, is_verified=True)
    except Puzzle.DoesNotExist:
        todays_puzzle = None

    # گرفتن 5 روز گذشته برای آرشیو پایین صفحه (اصلاح شده روی publish_date)
    past_puzzles = Puzzle.objects.filter(publish_date__lt=today, is_verified=True).order_by('-publish_date')[:5]

    # --- این خط اضافه شد ---
    # پیدا کردن معمای قبلی (جدیدترین معمای منتشر شده قبل از امروز)
    prev_puzzle = Puzzle.objects.filter(publish_date__lt=today, is_verified=True).order_by('-publish_date').first()

    context = {
        'todays_puzzle': todays_puzzle,
        'past_puzzles': past_puzzles,
        'prev_puzzle': prev_puzzle, # اینو فرستادیم تا دکمه‌اش روشن بشه!
    }
    return render(request, 'puzzles/home.html', context)


def play_puzzle(request, date_str):
    puzzle = get_object_or_404(Puzzle, publish_date=date_str, is_verified=True)
    today = timezone.localdate()

    past_puzzles = Puzzle.objects.filter(date__lt=today).order_by('-date')[:5]

    # --- کدهای جدید برای پیدا کردن معمای قبلی و بعدی ---
    # قبلی یعنی معمایی که تاریخش کوچیکتر از امروز باشه (اولین مورد بعد از مرتب‌سازی نزولی)
    prev_puzzle = Puzzle.objects.filter(publish_date__lt=puzzle.publish_date, is_verified=True).order_by(
        '-publish_date').first()    # بعدی یعنی معمایی که تاریخش بزرگتر از امروز باشه (اولین مورد بعد از مرتب‌سازی صعودی)
    next_puzzle = Puzzle.objects.filter(publish_date__gt=puzzle.publish_date, is_verified=True).order_by(
        'publish_date').first()
    # (اختیاری) اگر نمی‌خوای معماهای فردا و پس‌فردا لو برن، این شرط رو بذار:
    if next_puzzle and next_puzzle.date > today:
        next_puzzle = None

    context = {
        'puzzle': puzzle,
        'is_correct': None,
        'past_puzzles': past_puzzles,
        'prev_puzzle': prev_puzzle,  # ارسال به فرانت
        'next_puzzle': next_puzzle,  # ارسال به فرانت
    }

    if request.method == "POST":
        user_guess = request.POST.get('guess', '').strip()
        if user_guess.replace(" ", "") == puzzle.answer.replace(" ", ""):
            context['is_correct'] = True
            messages.success(request, "آفرین! درست حدس زدی.")
        else:
            context['is_correct'] = False
            messages.error(request, "اشتباه بود، دوباره تلاش کن.")

    return render(request, 'puzzles/play.html', context)

def reveal_letter(request, date_str):
    if request.method == "POST":
        puzzle = get_object_or_404(Puzzle, date=date_str)
        # گرفتن ایندکس‌هایی که کاربر درخواست کرده (اختیاری)
        # اما اینجا ما ساده عمل می‌کنیم، کلاینت درخواست میده، ما یه ایندکس رندوم میدیم

        answer_pure = puzzle.answer.replace(" ", "")
        indices = list(range(len(answer_pure)))

        # اینجا یه منطق ساده: یه اندیس رندوم و حرفش رو برمی‌گردونیم
        # فرانت‌اند باید مدیریت کنه که کدوم خونه‌ها خالی هستن و درخواست بده

        import json
        data = json.loads(request.body)
        exclude_indices = data.get('exclude', [])  # ایندکس‌هایی که کاربر پر کرده یا باز شدن

        available_indices = [i for i in indices if i not in exclude_indices]

        if not available_indices:
            return JsonResponse({'status': 'full'})

        chosen_index = random.choice(available_indices)
        char = answer_pure[chosen_index]

        return JsonResponse({
            'index': chosen_index,
            'char': char,
            'status': 'ok'
        })
    return JsonResponse({'status': 'error'})


def load_more_archive(request):
    offset = int(request.GET.get('offset', 5))  # پیش‌فرض ۵ تا چون ۵ تا اول رو خود صفحه رندر کرده
    limit = 7
    today = timezone.localdate()

    # گرفتن پازل‌های بعدی
    puzzles = Puzzle.objects.filter(date__lt=today).order_by('-date')[offset:offset + limit]

    data = []
    for p in puzzles:
        data.append({
            'url_date': p.date.strftime('%Y-%m-%d'),  # فرمت برای لینک
            'day_name': formats.date_format(p.date, "l"),  # نام روز (مثلا شنبه)
            'day_month': formats.date_format(p.date, "j F"),  # روز و ماه (مثلا 14 فوریه)
        })

    return JsonResponse({
        'puzzles': data,
        'has_more': len(puzzles) == limit  # اگر کمتر از لیمیت بود یعنی به تهش رسیدیم
    })


def archive_calendar(request, year=None, month=None):
    today = timezone.localdate()

    # اگر سال و ماه ارسال نشده بود، ماه فعلی رو در نظر بگیر
    if not year or not month:
        year = today.year
        month = today.month

    # محاسبه ماه قبل و بعد برای دکمه‌های تقویم
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # دریافت تمام معماهای این ماه از دیتابیس
    puzzles = Puzzle.objects.filter(publish_date__year=year, publish_date__month=month, is_verified=True)
    # تبدیل به یک دیکشنری برای جستجوی سریع (کلید: روز، مقدار: آبجکت معما)
    puzzle_dict = {p.publish_date.day: p for p in puzzles}

    # تنظیم شنبه به عنوان اولین روز هفته (در تقویم میلادی پایتون دوشنبه 0 است، پس شنبه 5 می‌شود)
    cal = calendar.Calendar(firstweekday=5)
    month_days = cal.monthdatescalendar(year, month)

    calendar_data = []
    for week in month_days:
        week_data = []
        for day_date in week:
            is_current_month = day_date.month == month
            puzzle = puzzle_dict.get(day_date.day) if is_current_month else None

            # معماهای روزهای آینده رو غیرفعال نشون میدیم
            is_future = day_date > today
            if is_future:
                puzzle = None

            week_data.append({
                'date': day_date,
                'is_current_month': is_current_month,
                'puzzle': puzzle,
                'is_today': day_date == today,
                'is_future': is_future
            })
        calendar_data.append(week_data)

    month_names = ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر",
                   "دسامبر"]

    context = {
        'year': year,
        'month': month,
        'month_name': month_names[month - 1],
        'calendar_data': calendar_data,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': today,
        'week_headers': ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']  # شنبه تا جمعه
    }
    return render(request, 'puzzles/calendar.html', context)


@login_required(login_url='/admin/login/')  # اگر لاگین نبود بره صفحه لاگین
def create_puzzle(request):
    if request.method == "POST":
        tagged_clue = request.POST.get('tagged_clue', '').strip()
        answer = request.POST.get('answer', '').strip()
        desc_def = request.POST.get('desc_definition', '').strip()
        desc_fod = request.POST.get('desc_fodder', '').strip()
        desc_ind = request.POST.get('desc_indicators', '').strip()

        if not tagged_clue or not answer:
            messages.error(request, "متن معما و پاسخ الزامی است!")
            return redirect('create_puzzle')

        # پیدا کردن بزرگترین تاریخ موجود در دیتابیس
        last_puzzle = Puzzle.objects.aggregate(Max('date'))['date__max']
        today = timezone.localdate()

        # اگر معمایی از قبل بود و تاریخش از امروز بزرگتر بود، برو روز بعدش
        # وگرنه از همین امروز شروع کن
        if last_puzzle and last_puzzle >= today:
            next_date = last_puzzle + timedelta(days=1)
        else:
            next_date = today

        # ذخیره در دیتابیس
        # در بخش ذخیره دیتابیس در ویوی create_puzzle:
        Puzzle.objects.create(
            author=request.user,
            tagged_clue=tagged_clue,
            answer=answer,
            desc_definition=desc_def,
            desc_fodder=desc_fod,
            desc_indicators=desc_ind,
            is_verified=False,  # منتظر تایید ادمین
            publish_date=None  # بدون تاریخ انتشار
        )
        messages.success(request, "معما با موفقیت ساخته شد و پس از بررسی منتشر خواهد شد.")

        messages.success(request,
                         f"معما با موفقیت ساخته شد و برای تاریخ {next_date.strftime('%Y-%m-%d')} زمان‌بندی شد!")
        return redirect('home')

    return render(request, 'puzzles/create.html')


from django.core.paginator import Paginator


@login_required(login_url='/admin/login/')
def my_puzzles(request):
    # گرفتن تمام معماهای کاربر (تایید شده یا نشده)
    puzzles_list = Puzzle.objects.filter(author=request.user).order_by('-id')
    paginator = Paginator(puzzles_list, 20)  # هر صفحه 20 عدد

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'puzzles/my_puzzles.html', {'page_obj': page_obj})


@login_required(login_url='/admin/login/')
def play_private(request, puzzle_id):
    # فقط خود کاربر میتونه معمای خودش رو با آیدی بازی کنه
    puzzle = get_object_or_404(Puzzle, id=puzzle_id, author=request.user)

    context = {
        'puzzle': puzzle,
        'is_correct': None,
        'is_private': True,  # این پرچم رو می‌فرستیم تا آرشیو و فلش‌ها نشون داده نشن
    }

    if request.method == "POST":
        user_guess = request.POST.get('guess', '').strip()
        if user_guess.replace(" ", "") == puzzle.answer.replace(" ", ""):
            context['is_correct'] = True
            messages.success(request, "آفرین! پاسخت کاملاً درست بود.")
        else:
            context['is_correct'] = False
            messages.error(request, "اشتباه بود، دوباره تلاش کن.")

    return render(request, 'puzzles/play.html', context)