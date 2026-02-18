from django.shortcuts import render

# Create your views here.
# puzzles/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from .models import Puzzle
from django.http import JsonResponse
import random
from django.http import JsonResponse
from django.utils import formats

def home(request):
    today = timezone.localdate()

    # گرفتن معمای امروز
    try:
        todays_puzzle = Puzzle.objects.get(date=today)
    except Puzzle.DoesNotExist:
        todays_puzzle = None

    # گرفتن 5 روز گذشته برای آرشیو پایین صفحه
    past_puzzles = Puzzle.objects.filter(date__lt=today).order_by('-date')[:5]

    context = {
        'todays_puzzle': todays_puzzle,
        'past_puzzles': past_puzzles,
    }
    return render(request, 'puzzles/home.html', context)

def play_puzzle(request, date_str):
    puzzle = get_object_or_404(Puzzle, date=date_str)

    # اضافه کردن این بخش برای گرفتن لیست آرشیو
    today = timezone.localdate()
    past_puzzles = Puzzle.objects.filter(date__lt=today).order_by('-date')[:5]

    context = {
        'puzzle': puzzle,
        'is_correct': None,
        'past_puzzles': past_puzzles,  # این رو حتما به کانتکست اضافه کن
        'user_guess': ''
    }

    if request.method == "POST":
        user_guess = request.POST.get('guess', '').strip()
        context['user_guess'] = user_guess

        # نرمال‌سازی ساده برای مقایسه
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