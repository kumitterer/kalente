import holidays
import pdfkit

from argparse import ArgumentParser
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from locale import setlocale, LC_ALL
from base64 import b64encode

from jinja2 import Environment, FileSystemLoader
from dateutil.parser import parse

import math

NO_LOGO = ""


def get_day(
    for_date: date = None,
    country_code: Optional[str] = None,
    date_format: str = "%b %d, %Y",
):
    for_date = for_date or date.today()
    day = for_date

    day_info = {
        "date_obj": day,
        "day": day.strftime("%A"),
        "date": day.strftime(date_format),
        "holiday": holidays.CountryHoliday(country_code, years=[for_date.year]).get(
            day
        ),
        "is_weekend": (day.weekday() in [5, 6]),
    }
    return day_info


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


def get_year(
    for_date: date = None,
    country_code: Optional[str] = None,
    date_format: str = "%b %d, %Y",
):
    for_date = for_date or date.today()
    year_start = for_date.replace(month=1, day=1)

    year_months = []

    for i in range(12):
        month = get_month(
            for_date=year_start.replace(month=i + 1),
            country_code=country_code,
            date_format=date_format,
        )
        year_months.append(month)

    return year_months


def generate_html(
    content, content_type, template_path: str = None, logo_path: str = None
):
    if not template_path:
        template_name = "{}.html".format(content_type)
        file_loader = FileSystemLoader(Path(__file__).parent.absolute() / "templates")
    else:
        template_name = template_path
        file_loader = FileSystemLoader()

    if logo_path is None:
        logo_path = Path(__file__).parent / "static" / "logo.png"

    if logo_path:
        # Let it throw, let it throw, let it throw...
        with Path(logo_path).open("rb") as logo_file:
            logo = b64encode(logo_file.read()).decode("utf-8")
            mime_type = (
                "image/png" if str(logo_path).endswith(".png") else "image/jpeg"
            )  # Doesn't matter much anyway.
            data_uri = f"data:image/png;base64,{logo}"

    env = Environment(loader=file_loader)
    template = env.get_template(template_name)

    context = {"logo": data_uri}

    if content_type == "yearly":
        return template.render(year=content, **context)
    elif content_type == "monthly":
        return template.render(month=content, **context)
    elif content_type == "weekly":
        return template.render(week=content, **context)
    elif content_type == "daily":
        return template.render(day=content, **context)
    else:
        raise ValueError("Invalid content type: {}".format(content_type))


def convert_html_to_pdf(content, output_filename, options=None):
    options.setdefault("page-size", "A4")
    options.setdefault("orientation", "Landscape")
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
        "--template",
        "-T",
        help="Template to use",
        required=False,
        default=None,
    )

    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument(
        "--type",
        "-t",
        help="Type of calendar to generate",
        required=False,
        choices=["weekly", "monthly", "daily", "yearly"],
        default="weekly",
    )
    type_group.add_argument(
        "--yearly",
        action="store_const",
        const="yearly",
        dest="type",
        help="Generate yearly calendar. Shortcut for --type yearly.",
    )
    type_group.add_argument(
        "--monthly",
        action="store_const",
        const="monthly",
        dest="type",
        help="Generate monthly calendar. Shortcut for --type monthly.",
    )
    type_group.add_argument(
        "--weekly",
        action="store_const",
        const="weekly",
        dest="type",
        help="Generate weekly calendar. This is the default. Shortcut for --type weekly.",
    )
    type_group.add_argument(
        "--daily",
        action="store_const",
        const="daily",
        dest="type",
        help="Generate daily calendar. Shortcut for --type daily.",
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

    logo_group = parser.add_mutually_exclusive_group()
    logo_group.add_argument(
        "--logo",
        help="Path to the logo to use",
        required=False,
        default=None,
    )
    logo_group.add_argument(
        "--no-logo",
        action="store_true",
        help="Don't use a logo",
        required=False,
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

        elif args.type == "yearly":
            count = end_date.year - for_date.year + 1

    if not args.type in ["daily", "weekly", "monthly", "yearly"]:
        raise ValueError(f"Invalid calendar type: {args.type}")

    if args.no_logo:
        logo_path = NO_LOGO
    else:
        logo_path = args.logo

    for i in range(count):
        data = (
            {
                "daily": get_day,
                "weekly": get_week,
                "monthly": get_month,
                "yearly": get_year,
            }[args.type]
        )(for_date, country_code, args.date_format)
        html_content = generate_html(data, args.type, args.template, logo_path)
        pages.append(html_content)
        for_date = {
            "daily": lambda x: x["date_obj"] + timedelta(days=1),
            "weekly": lambda x: x[-1]["date_obj"] + timedelta(days=1),
            "monthly": lambda x: x[1][0]["date_obj"] + timedelta(days=31),
            "yearly": lambda x: x[11][5][0]["date_obj"] + timedelta(days=365),
        }[args.type](data)

    conversion_options = {"orientation": "Portrait"} if args.type == "daily" else {}
    convert_html_to_pdf("\n".join(pages), args.output, options=conversion_options)


if __name__ == "__main__":
    main()
