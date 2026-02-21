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
from django.db.models import Q, F
from django.contrib.admin.views.decorators import staff_member_required
import jdatetime


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
        'prev_puzzle': prev_puzzle,  # اینو فرستادیم تا دکمه‌اش روشن بشه!
    }
    return render(request, 'puzzles/home.html', context)


# در فایل views.py

def play_puzzle(request, date_str):
    today = timezone.localdate()
    puzzle = get_object_or_404(Puzzle, publish_date=date_str, is_verified=True, publish_date__lte=today)

    past_puzzles = Puzzle.objects.filter(publish_date__lt=today, is_verified=True).order_by('-publish_date')[:5]
    prev_puzzle = Puzzle.objects.filter(publish_date__lt=puzzle.publish_date, is_verified=True).order_by(
        '-publish_date').first()
    next_puzzle = Puzzle.objects.filter(publish_date__gt=puzzle.publish_date, publish_date__lte=today,
                                        is_verified=True).order_by('publish_date').first()

    context = {
        'puzzle': puzzle,
        'is_correct': None,
        'past_puzzles': past_puzzles,
        'prev_puzzle': prev_puzzle,
        'next_puzzle': next_puzzle,

        'hint_def_used': 'false',
        'hint_fod_used': 'false',
        'hint_ind_used': 'false',
        'letters_revealed': 0,
    }

    if request.method == "POST":
        user_guess = request.POST.get('guess', '').strip()
        hint_def_used = request.POST.get('hint_def_used', 'false')
        hint_fod_used = request.POST.get('hint_fod_used', 'false')
        hint_ind_used = request.POST.get('hint_ind_used', 'false')
        try:
            letters_revealed = int(request.POST.get('letters_revealed', 0))
        except ValueError:
            letters_revealed = 0

        context['hint_def_used'] = hint_def_used
        context['hint_fod_used'] = hint_fod_used
        context['hint_ind_used'] = hint_ind_used
        context['letters_revealed'] = letters_revealed

        if user_guess.replace(" ", "") == puzzle.answer.replace(" ", ""):
            context['is_correct'] = True

            # محاسبه راهنمایی‌های استفاده شده توسط این کاربر
            current_hints_count = letters_revealed
            if hint_def_used == 'true': current_hints_count += 1
            if hint_fod_used == 'true': current_hints_count += 1
            if hint_ind_used == 'true': current_hints_count += 1

            # ارسال متغیر به تمپلیت برای نمایش در باکس آماری
            context['user_hints_used'] = current_hints_count

            puzzle.solve_count += 1
            puzzle.total_hints_used += current_hints_count
            puzzle.save()

            # دیگه پیام طولانی رو پاک کردیم، چون تو باکس نشونش میدیم
            messages.success(request, "آفرین!")
        else:
            context['is_correct'] = False
            messages.error(request, "اشتباه بود، دوباره تلاش کن.")

    return render(request, 'puzzles/play.html', context)


def reveal_letter(request, puzzle_id):
    if request.method == "POST":
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)

        # امنیت: فقط اگر معما تایید شده باشه، یا طرف خودش طراحش باشه، یا ادمین باشه بتونه حرفی رو لو بده
        if not puzzle.is_verified:
            if not request.user.is_authenticated or (puzzle.author != request.user and not request.user.is_staff):
                return JsonResponse({'status': 'error', 'message': 'Not authorized'})

        answer_pure = puzzle.answer.replace(" ", "")
        indices = list(range(len(answer_pure)))

        import json
        data = json.loads(request.body)
        exclude_indices = data.get('exclude', [])

        available_indices = [i for i in indices if i not in exclude_indices]

        if not available_indices:
            return JsonResponse({'status': 'full'})

        import random
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
    today_greg = timezone.localdate()
    today_jalali = jdatetime.date.fromgregorian(date=today_greg)

    if not year or not month:
        j_year = today_jalali.year
        j_month = today_jalali.month
    else:
        j_year = int(year)
        j_month = int(month)

    # محاسبه ماه قبل و بعد شمسی
    if j_month == 1:
        prev_month, prev_year = 12, j_year - 1
    else:
        prev_month, prev_year = j_month - 1, j_year

    if j_month == 12:
        next_month, next_year = 1, j_year + 1
    else:
        next_month, next_year = j_month + 1, j_year

    # محاسبه روزهای ماه شمسی
    first_day = jdatetime.date(j_year, j_month, 1)
    start_weekday = first_day.weekday()  # در این کتابخانه 0 یعنی شنبه

    if j_month <= 6:
        days_in_month = 31
    elif j_month <= 11:
        days_in_month = 30
    else:
        days_in_month = 29 if not first_day.isleap() else 30

    # گرفتن معماها از دیتابیس (تبدیل بازه شمسی به میلادی برای کوئری)
    start_greg = first_day.togregorian()
    end_greg = jdatetime.date(j_year, j_month, days_in_month).togregorian()
    puzzles = Puzzle.objects.filter(publish_date__gte=start_greg, publish_date__lte=end_greg, is_verified=True)

    # ساخت دیکشنری برای دسترسی سریع
    puzzle_dict = {jdatetime.date.fromgregorian(date=p.publish_date).day: p for p in puzzles}

    calendar_data = []
    week = []

    # پر کردن روزهای خالی اول ماه
    for _ in range(start_weekday):
        week.append({'is_current_month': False})

    for day in range(1, days_in_month + 1):
        current_jdate = jdatetime.date(j_year, j_month, day)
        is_future = current_jdate > today_jalali

        week.append({
            'is_current_month': True,
            'day_num': day,
            'greg_date_str': current_jdate.togregorian().strftime('%Y-%m-%d'),  # برای ساخت لینکِ بازی
            'puzzle': puzzle_dict.get(day) if not is_future else None,
            'is_today': current_jdate == today_jalali,
            'is_future': is_future
        })

        if len(week) == 7:
            calendar_data.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append({'is_current_month': False})
        calendar_data.append(week)

    month_names = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن',
                   'اسفند']

    context = {
        'year': j_year,
        'month': j_month,
        'month_name': month_names[j_month - 1],
        'calendar_data': calendar_data,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'week_headers': ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']
    }
    return render(request, 'puzzles/calendar.html', context)

@login_required(login_url='/login/')
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

        Puzzle.objects.create(
            author=request.user,
            tagged_clue=tagged_clue,
            answer=answer,
            desc_definition=desc_def,
            desc_fodder=desc_fod,
            desc_indicators=desc_ind,
            is_verified=False,  # منتظر تایید ادمین
            publish_date=None   # بدون تاریخ انتشار
        )

        messages.success(request, "معمای شما با موفقیت ثبت شد و در انتظار تایید ادمین است. می‌توانید معمای دیگری طراحی کنید!")

        return redirect('create_puzzle')

    return render(request, 'puzzles/create.html')

from django.core.paginator import Paginator


@login_required(login_url='/login/')
def my_puzzles(request):
    # گرفتن تمام معماهای کاربر (تایید شده یا نشده)
    puzzles_list = Puzzle.objects.filter(author=request.user).order_by('-id')
    paginator = Paginator(puzzles_list, 20)  # هر صفحه 20 عدد

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'puzzles/my_puzzles.html', {'page_obj': page_obj})


@login_required(login_url='/login/')
def play_private(request, puzzle_id):
    if request.user.is_staff:
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)
    else:
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


def get_next_available_date():
    """تابعی برای پیدا کردن اولین روزی که هیچ معمای تایید شده‌ای در آن ثبت نشده است"""
    today = timezone.localdate()
    # لیستی از تمام تاریخ‌های رزرو شده در آینده
    future_dates = set(Puzzle.objects.filter(
        publish_date__gt=today,
        is_verified=True
    ).values_list('publish_date', flat=True))

    # از فردا شروع به چک کردن می‌کنیم
    check_date = today + timedelta(days=1)
    while check_date in future_dates:
        check_date += timedelta(days=1)

    return check_date


@staff_member_required(login_url='login')
def admin_review_puzzles(request):
    today = timezone.localdate()

    if request.method == 'POST':
        puzzle_id = request.POST.get('puzzle_id')
        action = request.POST.get('action', 'verify')  # اکشن دیفالت: تایید کردن
        puzzle = get_object_or_404(Puzzle, id=puzzle_id)

        if action == 'verify':
            publish_date_str = request.POST.get('publish_date')
            puzzle.is_verified = True
            puzzle.publish_date = publish_date_str
            puzzle.save()
            messages.success(request, f"معمای «{puzzle.answer}» برای تاریخ {publish_date_str} زمان‌بندی شد.")
        elif action == 'unverify':
            # لغو تایید
            puzzle.is_verified = False
            puzzle.publish_date = None
            puzzle.save()
            messages.warning(request, f"تایید معمای «{puzzle.answer}» لغو شد و به لیست در انتظار بررسی بازگشت.")

        # ریدایرکت به همون صفحه‌ای که توش بودیم (تا سورت و فیلترها حفظ بشن)
        return redirect(request.get_full_path())

    # چک کردن اینکه آیا ادمین دکمه "نمایش همه" رو زده یا نه
    show_all = request.GET.get('show_all') == 'true'

    if show_all:
        puzzles = Puzzle.objects.all()
    else:
        # فقط در انتظار تاییدها و آینده‌ها
        puzzles = Puzzle.objects.filter(
            Q(is_verified=False) | Q(is_verified=True, publish_date__gt=today)
        )

    sort_by = request.GET.get('sort', '-date')
    allowed_sorts = ['date', '-date', 'publish_date', '-publish_date', 'author__username', '-author__username',
                     'is_verified', '-is_verified']

    if sort_by in allowed_sorts:
        if 'publish_date' in sort_by:
            if sort_by.startswith('-'):
                puzzles = puzzles.order_by(F('publish_date').desc(nulls_last=True))
            else:
                puzzles = puzzles.order_by(F('publish_date').asc(nulls_last=True))
        else:
            puzzles = puzzles.order_by(sort_by)
    else:
        puzzles = puzzles.order_by('-date')

    next_date = get_next_available_date()

    context = {
        'puzzles': puzzles,
        'next_available_date': next_date.strftime('%Y-%m-%d'),
        'current_sort': sort_by,
        'show_all': show_all  # فرستادن این متغیر به فرانت
    }
    return render(request, 'puzzles/admin_review.html', context)