import holidays
import pdfkit

from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from locale import setlocale, LC_ALL

from jinja2 import Environment, FileSystemLoader
from dateutil.parser import parse

import math


def get_month(
    for_date: date = None,
    country_code: Optional[str] = None,
    date_format: str = "%b %d, %Y",
):
    for_date = for_date or date.today()
    month_start = for_date.replace(day=1)

    month_weeks = []

    for i in range(6):
        week = get_week(
            for_date=month_start + timedelta(days=i * 7),
            country_code=country_code,
            date_format=date_format,
        )

        if (
            week[0]["date_obj"].month != for_date.month
            and week[-1]["date_obj"].month != for_date.month
        ):
            break

        month_weeks.append(week)

    return month_weeks


def get_week(
    for_date: date = None,
    country_code: Optional[str] = None,
    date_format: str = "%b %d, %Y",
):
    week_days = []

    for_date = for_date or date.today()
    week_start = for_date - timedelta(days=for_date.weekday())
    week_end = week_start + timedelta(days=6)

    if country_code:
        holiday_list = holidays.CountryHoliday(
            country_code, years=[for_date.year, week_end.year, week_start.year]
        )
    else:
        holiday_list = {}

    for i in range(7):
        day = week_start + timedelta(days=i)
        day_info = {
            "date_obj": day,
            "day": day.strftime("%A"),
            "date": day.strftime(date_format),
            "holiday": holiday_list.get(day),
            "is_weekend": (day.weekday() in [5, 6]),
        }
        week_days.append(day_info)
    return week_days


def generate_monthly_html(month):
    file_loader = FileSystemLoader(Path(__file__).parent.absolute() / "templates")
    env = Environment(loader=file_loader)
    template = env.get_template("monthly.html")
    return template.render(
        month=month, month_obj=month[1][0]["date_obj"]
    )


def generate_weekly_html(week):
    file_loader = FileSystemLoader(Path(__file__).parent.absolute() / "templates")
    env = Environment(loader=file_loader)
    template = env.get_template("weekly.html")
    return template.render(week=week)


def convert_html_to_pdf(content, output_filename):
    options = {
        "page-size": "A4",
        "orientation": "Landscape",
    }
    pdfkit.from_string(content, output_filename, options=options)


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--country",
        "-c",
        help="Country code for the holidays",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--output", "-o", help="Output filename", required=False, default="calendar.pdf"
    )
    parser.add_argument(
        "--date",
        "-d",
        help="Date to generate the calendar for",
        required=False,
        default=None,
    )
    parser.add_argument(
        "--date-format",
        "-f",
        help="Date format to use",
        required=False,
        default="%b %d, %Y",
    )
    parser.add_argument(
        "--type",
        "-t",
        help="Type of calendar to generate",
        required=False,
        default="weekly",
    )

    count_group = parser.add_mutually_exclusive_group()
    count_group.add_argument(
        "--count",
        "-n",
        help="Number of subsequent calendars to generate",
        type=int,
        required=False,
    )
    count_group.add_argument(
        "--end-date",
        "-e",
        help="End date for the calendar",
        required=False,
        default=None,
    )

    args = parser.parse_args()

    # Set locale to en_US.UTF-8 – for now, only English is supported
    setlocale(LC_ALL, "en_US.UTF-8")

    if args.country:
        country_code = args.country.upper()
        assert (
            country_code in holidays.list_supported_countries()
        ), f"Country code {country_code} is not supported"

    else:
        country_code = None

    if args.date:
        try:
            for_date = parse(args.date).date()
        except ValueError:
            raise ValueError(f"Unrecognized date format {args.date}")
    else:
        for_date = None

    pages = []

    count = 1

    if args.count:
        count = args.count

    elif args.end_date:
        end_date = parse(args.end_date).date()

        if args.type == "weekly":
            count = math.ceil((end_date - for_date).days / 7)

        elif args.type == "monthly":
            count = 0
            start_date = for_date.replace(day=1)

            while start_date <= end_date:
                count += 1

                try:
                    start_date = start_date.replace(month=start_date.month + 1)
                except ValueError:
                    start_date = start_date.replace(year=start_date.year + 1, month=1)

    if args.type == "weekly":
        for i in range(count):
            week = get_week(for_date, country_code, args.date_format)
            html_content = generate_weekly_html(week)
            pages.append(html_content)
            for_date = week[-1]["date_obj"] + timedelta(days=1)
    elif args.type == "monthly":
        for i in range(count):
            month = get_month(for_date, country_code, args.date_format)
            html_content = generate_monthly_html(month)
            pages.append(html_content)
            for_date = month[1][0]["date_obj"] + timedelta(days=31)
    else:
        raise NotImplementedError(f"Calendar type {args.type} is not supported")

    convert_html_to_pdf("\n".join(pages), args.output)


if __name__ == "__main__":
    main()
