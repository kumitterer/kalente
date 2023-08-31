import holidays
import pdfkit

from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader
from dateutil.parser import parse


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
            "day": day.strftime("%A"),
            "date": day.strftime(date_format),
            "holiday": holiday_list.get(day),
            "is_weekend": (day.weekday() in [5, 6]),
        }
        week_days.append(day_info)
    return week_days


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

    args = parser.parse_args()

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

    if args.type != "weekly":
        raise NotImplementedError(f"Calendar type {args.type} is not supported")

    week = get_week(for_date, country_code, args.date_format)
    html_content = generate_weekly_html(week)
    convert_html_to_pdf(html_content, args.output)


if __name__ == "__main__":
    main()
