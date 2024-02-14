# Kalente

<img src="src/kalente/static/logo.png" alt="Kalente logo" width="200" height="200" align="right">

Kalente is a simple Python script for generating PDF calendars.

It can be used to generate weekly and monthly calendars at the moment, and it
will be extended to support yearly calendars as well.

Currently, Kalente can only generate calendars in English, but support for
other languages will be added in the future. Also, calendars are currently
generated in A4 landscape format, but support for other formats will be added
in the future. If you can help with any of these, please feel free to open a
pull request.

## Requirements

Kalente should work with any Python version from 3.8 onwards.

It also requires wkhtmltopdf to be installed on your system. You can find
instructions on how to install it on your system
[on the project's website](https://wkhtmltopdf.org/).

## Installation

First, set up a virtual environment for Kalente:

```bash
python -m venv venv
```

Then, activate the virtual environment:

```bash
source venv/bin/activate
```

You can install Kalente using pip:

```bash
pip install kalente
```

## Usage

Kalente can be used as a command line tool to generate calendars. You can
generate weekly calendars using the following command:

```bash
kalente --type weekly --date 2021-01-01 --output weekly.pdf
```

This will generate a weekly calendar for the week of January 1st, 2021. The
calendar will be saved to the file `weekly.pdf`.

You can also generate monthly calendars using the following command:

```bash
kalente --type monthly --date 2021-08-01 --output monthly.pdf
```

This will generate a monthly calendar for August 2021 and save it to the file
`monthly.pdf`.

You can also use the `--help` option to get more information about the
available options:

```bash
kalente --help
```

For example, you may want to look into the `--end-date` and `--count` options
to generate calendars for multiple weeks or months.

## License

Kalente is licensed under the MIT license. See the [LICENSE](LICENSE) file for
more information.
