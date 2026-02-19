import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ramzgosha.settings')
django.setup()

from puzzles.models import Puzzle

def update_puzzles():
    puzzles = Puzzle.objects.all()
    count = 0
    for p in puzzles:
        if not p.is_verified:
            p.is_verified = True
            p.publish_date = p.date  # انتقال تاریخ قدیمی به فیلد انتشار رسمی
            p.save()
            count += 1
    print(f"✅ تعداد {count} معما با موفقیت تایید و بروزرسانی شدند.")

if __name__ == '__main__':
    update_puzzles()