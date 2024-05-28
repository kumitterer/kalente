import holidays
import pdfkit

from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from base64 import b64encode

from jinja2 import Environment, FileSystemLoader


class Calendar:
    def __init__(self, country_code: Optional[str] = None, date_format: str = "%b %d, %Y"):
        self.country_code = country_code
        self.date_format = date_format

    def get_day(self, for_date: date = None):
        for_date = for_date or date.today()
        day = for_date

        day_info = {
            "date_obj": day,
            "day": day.strftime("%A"),
            "date": day.strftime(self.date_format),
            "holiday": holidays.CountryHoliday(self.country_code, years=[for_date.year]).get(day),
            "is_weekend": (day.weekday() in [5, 6]),
        }
        return day_info

    def get_week(self, for_date: date = None):
        week_days = []

        for_date = for_date or date.today()
        week_start = for_date - timedelta(days=for_date.weekday())
        week_end = week_start + timedelta(days=6)

        if self.country_code:
            holiday_list = holidays.CountryHoliday(
                self.country_code, years=[for_date.year, week_end.year, week_start.year]
            )
        else:
            holiday_list = {}

        for i in range(7):
            day = week_start + timedelta(days=i)
            day_info = {
                "date_obj": day,
                "day": day.strftime("%A"),
                "date": day.strftime(self.date_format),
                "holiday": holiday_list.get(day),
                "is_weekend": (day.weekday() in [5, 6]),
            }
            week_days.append(day_info)
        return week_days

    def get_month(self, for_date: date = None):
        for_date = for_date or date.today()
        month_start = for_date.replace(day=1)

        month_weeks = []

        for i in range(6):
            week = self.get_week(for_date=month_start + timedelta(days=i * 7))

            if (
                week[0]["date_obj"].month != for_date.month
                and week[-1]["date_obj"].month != for_date.month
            ):
                break

            month_weeks.append(week)

        return month_weeks

    def get_year(self, for_date: date = None):
        for_date = for_date or date.today()
        year_start = for_date.replace(month=1, day=1)

        year_months = []

        for i in range(12):
            month = self.get_month(for_date=year_start.replace(month=i + 1))
            year_months.append(month)

        return year_months

    @staticmethod
    def generate_html(content, content_type, template_path: str = None, logo_path: str = None):
        if not template_path:
            template_name = "{}.html".format(content_type)
            file_loader = FileSystemLoader(Path(__file__).parent.parent.absolute() / "templates")
        else:
            template_name = template_path
            file_loader = FileSystemLoader(template_path)

        if logo_path is None:
            logo_path = Path(__file__).parent.parent.absolute() / "static" / "logo.png"

        if str(logo_path).startswith("data:"):
            data_uri = logo_path

        elif logo_path:
            with Path(logo_path).open("rb") as logo_file:
                logo = b64encode(logo_file.read()).decode("utf-8")
                mime_type = (
                    "image/png" if str(logo_path).endswith(".png") else "image/jpeg"
                )  
                data_uri = f"data:{mime_type};base64,{logo}"

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

    @staticmethod
    def convert_html_to_pdf(content, output_filename, options=None):
        options.setdefault("page-size", "A4")
        options.setdefault("orientation", "Landscape")
        pdfkit.from_string(content, output_filename, options=options)
