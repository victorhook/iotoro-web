from django.utils import timezone


def format_date(date: timezone) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")
    