import holidays

from argparse import ArgumentParser
from datetime import timedelta
from locale import setlocale, LC_ALL

from dateutil.parser import parse

from .classes.calendar import Calendar

import math

NO_LOGO = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


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

    if args.type not in ["daily", "weekly", "monthly", "yearly"]:
        raise ValueError(f"Invalid calendar type: {args.type}")

    if args.no_logo:
        logo_path = NO_LOGO
    else:
        logo_path = args.logo

    generator = Calendar(country_code, args.date_format)

    for i in range(count):
        data = (
            {
                "daily": generator.get_day,
                "weekly": generator.get_week,
                "monthly": generator.get_month,
                "yearly": generator.get_year,
            }[args.type]
        )(for_date)
        html_content = Calendar.generate_html(data, args.type, args.template, logo_path)
        pages.append(html_content)
        for_date = {
            "daily": lambda x: x["date_obj"] + timedelta(days=1),
            "weekly": lambda x: x[-1]["date_obj"] + timedelta(days=1),
            "monthly": lambda x: x[1][0]["date_obj"] + timedelta(days=31),
            "yearly": lambda x: x[-1][-1][0]["date_obj"] + timedelta(days=365),
        }[args.type](data)

    conversion_options = {"orientation": "Portrait"} if args.type == "daily" else {}
    Calendar.convert_html_to_pdf(
        "\n".join(pages), args.output, options=conversion_options
    )


if __name__ == "__main__":
    main()
