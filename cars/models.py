from django.db import models


class Car(models.Model):
    CAR_TYPES = [
        ('sedan', 'Седан'),
        ('suv', 'Внедорожник'),
        ('coupe', 'Купе'),
        ('hatchback', 'Хэтчбек'),
        ('sport', 'Спорткар'),
    ]

    FUEL_TYPES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Электрический'),
        ('hybrid', 'Гибрид'),
    ]

    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    car_type = models.CharField(max_length=20, choices=CAR_TYPES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPES)
    engine_volume = models.FloatField()
    power = models.IntegerField()
    image = models.ImageField(upload_to='cars/', blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"