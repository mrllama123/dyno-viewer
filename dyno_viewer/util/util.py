import csv
import io
from decimal import Decimal


def chunk(list_to_split, amount):
    """split a list into n amount"""
    for i in range(0, len(list_to_split), amount):
        yield list_to_split[i : i + amount]


def format_output(value):
    if isinstance(value, Decimal):
        return str(value)

    return value


def output_to_csv_str(iterable):
    output = io.StringIO()
    iterable = [format_output(item) for item in iterable]
    writer = csv.writer(output)
    writer.writerow(iterable)
    return output.getvalue()
