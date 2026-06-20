from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    name = models.CharField(max_length=200, verbose_name="Номи фан")
    description = models.TextField(blank=True, verbose_name="Тавсифи фан")
    timer_minutes = models.PositiveIntegerField(default=5, verbose_name="Вақт (дақиқа)")

    class Meta:
        verbose_name = "Фан"
        verbose_name_plural = "Фанҳо"

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Истифодабаранда"
        )
    subjects = models.ManyToManyField(
        Subject,
        blank=True,
        related_name="users",
        verbose_name="Фанҳои иҷозатдодашуда"
    )

    class Meta:
        verbose_name = "Профил"
        verbose_name_plural = "Профилҳо"

    def __str__(self):
        return self.user.username


class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Осон'),
        ('medium', 'Миёна'),
        ('hard', 'Мушкил'),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Фан"
    )
    text = models.TextField(verbose_name="Матни савол")
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        verbose_name="Сатҳи савол"
    )

    option_a = models.CharField(max_length=255, verbose_name="Вариант A")
    option_b = models.CharField(max_length=255, verbose_name="Вариант B")
    option_c = models.CharField(max_length=255, blank=True, verbose_name="Вариант C")
    option_d = models.CharField(max_length=255, blank=True, verbose_name="Вариант D")

    CORRECT_CHOICES = [
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
    ]
    correct_option = models.CharField(
        max_length=1,
        choices=CORRECT_CHOICES,
        verbose_name="Ҷавоби дуруст"
    )

    class Meta:
        verbose_name = "Савол"
        verbose_name_plural = "Саволҳо"

    def __str__(self):
        return f"{self.subject.name} | {self.get_difficulty_display()}"


class Result(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Фан")
    score = models.PositiveIntegerField(verbose_name="Хол")
    total_questions = models.PositiveIntegerField(verbose_name="Ҳамаи саволҳо")

    # 🔹 AI analysis
    level = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Сатҳи дониш"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Тавсифи AI"
    )
    recommendation = models.TextField(
        blank=True,
        null=True,
        verbose_name="Тавсияи AI"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Сана")

    class Meta:
        verbose_name = "Натиҷа"
        verbose_name_plural = "Натиҷаҳо"

    def __str__(self):
        return f"{self.user.username} – {self.subject.name} ({self.score}/{self.total_questions})"