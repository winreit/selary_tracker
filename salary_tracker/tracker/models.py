from django.utils import timezone

from django.db import models

from django.db import models
from django.contrib.auth.models import User


# Типы работ с ценами
class WorkType(models.Model):
    name = models.CharField('Название работы', max_length=100, unique=True)
    price = models.IntegerField('Цена')

    def __str__(self):
        return self.name


# Профиль пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    register_date = models.DateTimeField('Дата регистрации', auto_now_add=True)

    def __str__(self):
        return self.user.username


# Выполненные работы
class Work(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    work_type = models.ForeignKey(WorkType, on_delete=models.CASCADE, verbose_name='Тип работы')
    work_number = models.CharField('Номер работы', max_length=15, blank=True, null=True, unique=False)
    date = models.DateTimeField('Дата', auto_now_add=True)
    day = models.IntegerField('День', blank=True, null=True)
    month = models.IntegerField('Месяц')
    year = models.IntegerField('Год')

    def save(self, *args, **kwargs):
        if not self.pk:
            now = timezone.now()
            self.day = now.day
            self.month = now.month
            self.year = now.year
        super().save(*args, **kwargs)


    class Meta:
        ordering = ['-date']
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'

    def __str__(self):
        return f"{self.user.username} - {self.work_type.name}"


# Итоги по месяцам
class MonthlyTotal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    month = models.IntegerField('Месяц')
    year = models.IntegerField('Год')
    total = models.IntegerField('Сумма')
    save_date = models.DateTimeField('Дата сохранения', auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month']
        verbose_name = 'Итог за месяц'
        verbose_name_plural = 'Итоги по месяцам'

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}: {self.total} руб."