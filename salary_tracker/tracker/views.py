from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import WorkType, Work, MonthlyTotal
import datetime


# Инициализация типов работ
def initialize_work_types():
    TYPES_RABOT = {
        'доплата': 363,
        'подключение интернета': 94,
        'подключение коннектор': 1212,
        'подключение сварка': 1446,
        'подключение доп': 556,
        'кроссировка': 550,
        'обслуживание': 293,
        'обслуживание область': 439,
        'подключение тв': 176,
        'доставка симкарты': 410,
        'демонтаж онт': 105,
        'демонтаж прочих': 76,
        'замена оборудования': 299,
        'камера': 158,
        'подключение кабель проложен': 492,
        'подключение телефона': 82
    }

    for name, price in TYPES_RABOT.items():
        WorkType.objects.get_or_create(name=name, defaults={'price': price})


# Главная страница
@login_required
def dashboard(request):
    initialize_work_types()

    now = timezone.now()
    month_total = Work.objects.filter(
        user=request.user,
        month=now.month,
        year=now.year
    ).aggregate(total=Sum('work_type__price'))['total'] or 0

    all_time_total = get_all_time_total(request.user)
    last_works = Work.objects.filter(user=request.user).order_by('-date')[:5]  # Последние 5 работ

    context = {
        'month_total': month_total,
        'all_time_total': all_time_total,
        'last_works': last_works,  # Добавляем в контекст
    }
    return render(request, 'tracker/dashboard.html', context)

# Добавление работы
@login_required
def add_work(request):
    if request.method == 'POST':
        work_type_id = request.POST.get('work_type')
        work_number = request.POST.get('work_number')
        work_type = WorkType.objects.get(id=work_type_id)

        now = timezone.now()
        Work.objects.create(
            user=request.user,
            work_type=work_type,
            work_number=work_number,
            month=now.month,
            year=now.year
        )

        messages.success(request, f'✅ Добавлено: {work_type.name} - {work_type.price} руб.')
        return redirect('dashboard')

    work_types = WorkType.objects.all()
    return render(request, 'tracker/add_work.html', {'work_types': work_types})


# Удаление последней работы
@login_required
def delete_last_work(request):
    last_work = Work.objects.filter(user=request.user).order_by('-date').first()

    if last_work:
        work_type_name = last_work.work_type.name
        price = last_work.work_type.price
        last_work.delete()
        messages.warning(request, f'❌ Удалено: {work_type_name} - {price} руб.')
    else:
        messages.warning(request, '❌ Нечего удалять')

    return redirect('dashboard')


# Сохранение месяца
@login_required
def save_month(request):
    now = timezone.now()
    works = Work.objects.filter(
        user=request.user,
        month=now.month,
        year=now.year
    )

    total = works.aggregate(total=Sum('work_type__price'))['total'] or 0

    if total > 0:
        MonthlyTotal.objects.create(
            user=request.user,
            month=now.month,
            year=now.year,
            total=total
        )
        works.delete()
        messages.success(request, f'💾 Месяц сохранен! Сумма: {total} руб.')
    else:
        messages.warning(request, 'ℹ️ Нет данных для сохранения за текущий месяц')

    return redirect('dashboard')


# Статистика за месяц
@login_required
def month_stats(request):
    now = timezone.now()
    month_total = Work.objects.filter(
        user=request.user,
        month=now.month,
        year=now.year
    ).aggregate(total=Sum('work_type__price'))['total'] or 0

    context = {
        'month_total': month_total,
        'current_month': now.month,
        'current_year': now.year,
    }
    return render(request, 'tracker/month_stats.html', context)


# Статистика за все время
@login_required
def all_time_stats(request):
    all_time_total = get_all_time_total(request.user)
    monthly_totals = MonthlyTotal.objects.filter(user=request.user).order_by('-year', '-month')

    context = {
        'all_time_total': all_time_total,
        'monthly_totals': monthly_totals,
    }
    return render(request, 'tracker/all_time_stats.html', context)


# Вспомогательная функция для расчета общей суммы
def get_all_time_total(user):
    works_total = Work.objects.filter(user=user).aggregate(
        total=Sum('work_type__price')
    )['total'] or 0

    monthly_total = MonthlyTotal.objects.filter(user=user).aggregate(
        total=Sum('total')
    )['total'] or 0

    return works_total + monthly_total