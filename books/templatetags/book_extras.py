import datetime
from django import template
from books.models import Book

register = template.Library()


@register.filter
def price_rub(value):
    """Форматирует цену"""
    return f"{int(value):,} ₽".replace(",", " ")

@register.filter
def short_text(value, words=10):
    """Обрезает текст до указанного количества слов"""
    words_list = value.split()
    return " ".join(words_list[:words]) + "..."

@register.filter
def add_vat(value):
    """Добавляет НДС 20%"""
    res = float(value) * 1.2
    return int(res)


@register.simple_tag
def books_count():
    """Возвращает общее количество книг"""
    return Book.objects.count()

@register.simple_tag
def current_year():
    """Возвращает текущий год"""
    return datetime.datetime.now().year

@register.simple_tag
def get_welcome_message(user_name="Гость"):
    """Возвращает приветствие в зависимости от времени суток"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        status = "Доброе утро"
    elif hour < 18:
        status = "Добрый день"
    else:
        status = "Добрый вечер"
    return f"{status}, {user_name}!"