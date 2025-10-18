from django.db import models
from api.models import User

class Car(models.Model):
    CAR_TYPES = [
        ('sedan', 'Седан'),
        ('suv', 'Внедорожник'),
        ('coupe', 'Купе'),
        ('hatchback', 'Хэтчбек'),
        ('sport', 'Спорткар'),
        ('electric', 'Электромобиль'),
    ]

    FUEL_TYPES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Электрический'),
        ('hybrid', 'Гибрид'),
    ]

    TRANSMISSION_TYPES = [
        ('manual', 'Механическая'),
        ('automatic', 'Автоматическая'),
        ('tiptronic', 'Типтроник'),
        ('robot', 'Роботизированная'),
    ]

    CONDITION_TYPES = [
        ('new', 'Новый'),
        ('used', 'Б/у'),
    ]

    STEERING_TYPES = [
        ('left', 'Слева'),
        ('right', 'Справа'),
    ]

    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    year = models.IntegerField(verbose_name='Год выпуска')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    car_type = models.CharField(max_length=20, choices=CAR_TYPES, verbose_name='Тип кузова')
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES, verbose_name='Тип топлива')
    engine_volume = models.FloatField(verbose_name='Объем двигателя', blank=True, null=True)
    power = models.IntegerField(verbose_name='Мощность (л.с.)', blank=True, null=True)
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, verbose_name='Коробка передач')
    mileage = models.IntegerField(verbose_name='Пробег (км)', blank=True, null=True)
    condition = models.CharField(max_length=10, choices=CONDITION_TYPES, default='used', verbose_name='Состояние')
    steering = models.CharField(max_length=10, choices=STEERING_TYPES, default='left', verbose_name='Руль')
    color = models.CharField(max_length=50, verbose_name='Цвет', blank=True)
    installment = models.BooleanField(default=True, verbose_name='Рассрочка')
    phone = models.CharField(max_length=20, default='+996700727745', verbose_name='Телефон')
    image = models.ImageField(upload_to='cars/', blank=True, null=True, verbose_name='Главное фото')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    views = models.IntegerField(default=0, verbose_name='Просмотры')

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']

class CarImage(models.Model):
    car = models.ForeignKey(Car, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='cars/gallery/', verbose_name='Фото')

    def __str__(self):
        return f"Image for {self.car.brand} {self.car.model}"

class Ad(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='ads/', null=True, blank=True, verbose_name='Изображение')
    installment_info = models.CharField(max_length=255, null=True, blank=True, verbose_name='Инфо о рассрочке')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Рекламное объявление'
        verbose_name_plural = 'Рекламные объявления'