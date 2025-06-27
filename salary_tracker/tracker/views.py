from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count
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

    # Статистика за сегодня
    today_works = Work.objects.filter(
        user=request.user,
        day=now.day,
        month=now.month,
        year=now.year
    )
    today_total = sum(w.work_type.price for w in today_works)

    # Статистика за месяц
    month_total = Work.objects.filter(
        user=request.user,
        month=now.month,
        year=now.year
    ).aggregate(total=Sum('work_type__price'))['total'] or 0

    # Общая статистика
    all_time_total = get_all_time_total(request.user)

    # Последние 5 работ
    last_works = Work.objects.filter(user=request.user).order_by('-date')[:5]

    # Последние 7 дней с работами (с проверкой на None)
    last_days_query = Work.objects.filter(
        user=request.user,
        day__isnull=False  # Добавляем фильтр для исключения None
    ).values(
        'day', 'month', 'year'
    ).annotate(
        total=Sum('work_type__price'),
        count=Count('id')
    ).order_by('-year', '-month', '-day')[:7]

    # Преобразуем QuerySet в список словарей с проверкой значений
    last_days = []
    for day in last_days_query:
        if all(day[key] is not None for key in ['day', 'month', 'year']):
            last_days.append({
                'day': int(day['day']),
                'month': int(day['month']),
                'year': int(day['year']),
                'total': day['total'],
                'count': day['count']
            })

    context = {
        'today_total': today_total,
        'month_total': month_total,
        'all_time_total': all_time_total,
        'last_works': last_works,
        'last_days': last_days,
        'current_date': now.date()
    }
    return render(request, 'tracker/dashboard.html', context)

# Статистика за день
@login_required
def day_stats(request, year=None, month=None, day=None):
    now = timezone.now()
    year = year or now.year
    month = month or now.month
    day = day or now.day

    works = Work.objects.filter(
        user=request.user,
        day=day,
        month=month,
        year=year
    ).select_related('work_type')

    total = sum(w.work_type.price for w in works)

    context = {
        'works': works,
        'total': total,
        'current_date': f"{day}.{month}.{year}",
        'prev_day': get_prev_day(year, month, day),
        'next_day': get_next_day(year, month, day),
    }
    return render(request, 'tracker/day_stats.html', context)


def get_prev_day(year, month, day):
    try:
        date = datetime.date(year, month, day) - datetime.timedelta(days=1)
        return {'year': date.year, 'month': date.month, 'day': date.day}
    except ValueError:
        return None


def get_next_day(year, month, day):
    try:
        date = datetime.date(year, month, day) + datetime.timedelta(days=1)
        return {'year': date.year, 'month': date.month, 'day': date.day}
    except ValueError:
        return None

# Добавление работы
@login_required
def add_work(request):
    if request.method == 'POST':
        work_type_id = request.POST.get('work_type')
        work_number = request.POST.get('work_number', '').strip()

        if not work_number:
            messages.error(request, 'Номер работы не может быть пустым')
            return redirect('add_work')


        try:
            work_type = WorkType.objects.get(id=work_type_id)

            # Создаем работу - метод save() модели автоматически установит дату
            Work.objects.create(
                user=request.user,
                work_type=work_type,
                work_number=work_number
            )

            messages.success(request, f'✅ Добавлено: {work_number} - {work_type.name} - {work_type.price} руб.')
            return redirect('add_work')

        except WorkType.DoesNotExist:
            messages.error(request, 'Выбранный тип работы не существует')
            return redirect('add_work')

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

def get_prev_day(year, month, day):
    try:
        date = datetime.date(year, month, day) - datetime.timedelta(days=1)
        return {'year': date.year, 'month': date.month, 'day': date.day}
    except ValueError:
        return None

def get_next_day(year, month, day):
    try:
        date = datetime.date(year, month, day) + datetime.timedelta(days=1)
        return {'year': date.year, 'month': date.month, 'day': date.day}
    except ValueError:
        return None