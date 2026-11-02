
import argparse
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERL_SCRIPT = ROOT / "perl" / "normalize_text.pl"

REQUIRED_COLUMNS = {"name", "email", "country_code"}


def normalize_text(value):
    """Normalize whitespace by calling our Perl utility."""
    result = subprocess.run(
        ["perl", str(PERL_SCRIPT)],
        input=value,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout


def validate_record(record):
    """Return a list of validation errors for one record."""
    errors = []

    for field in REQUIRED_COLUMNS:
        if not record.get(field, "").strip():
            errors.append(f"Missing {field}")

    email = record.get("email", "").strip()
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append("Invalid email")

    country = record.get("country_code", "").strip()
    if country and not re.fullmatch(r"[A-Z]{2}", country):
        errors.append("Invalid country_code: expected two uppercase letters")

    return errors


def clean_csv(input_file, output_dir):
    """Clean a CSV file and write valid rows and rejected rows."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_file = output_dir / "cleaned.csv"
    errors_file = output_dir / "errors.csv"

    seen_emails = set()
    cleaned_count = 0
    rejected_count = 0

    with input_file.open(
        "r", newline="", encoding="utf-8-sig"
    ) as source:
        reader = csv.DictReader(source)

        if not reader.fieldnames:
            raise ValueError("Input CSV is empty or has no header")

        # Normalize column names and reject missing required columns.
        reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                "Missing required columns: " + ", ".join(sorted(missing))
            )

        with cleaned_file.open(
            "w", newline="", encoding="utf-8"
        ) as clean_output, errors_file.open(
            "w", newline="", encoding="utf-8"
        ) as error_output:
            clean_writer = csv.DictWriter(
                clean_output, fieldnames=reader.fieldnames
            )
            error_writer = csv.DictWriter(
                error_output,
                fieldnames=["row_number", "error"] + reader.fieldnames,
            )

            clean_writer.writeheader()
            error_writer.writeheader()

            for row_number, row in enumerate(reader, start=2):
                # Normalize every field using the Perl script.
                row = {
                    key: normalize_text(value or "")
                    for key, value in row.items()
                    if key is not None
                }

                # Compare email addresses case-insensitively.
                email = row.get("email", "").lower()
                row["email"] = email

                problems = validate_record(row)

                if email and email in seen_emails:
                    problems.append("Duplicate email")

                if problems:
                    error_writer.writerow({
                        "row_number": row_number,
                        "error": "; ".join(problems),
                        **row,
                    })
                    rejected_count += 1
                else:
                    clean_writer.writerow(row)
                    if email:
                        seen_emails.add(email)
                    cleaned_count += 1

    return cleaned_count, rejected_count


def main():
    parser = argparse.ArgumentParser(
        description="Clean and validate employee CSV files"
    )
    parser.add_argument("input", type=Path, help="Input CSV file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "output",
        help="Directory for cleaned.csv and errors.csv",
    )
    args = parser.parse_args()

    try:
        cleaned, rejected = clean_csv(args.input, args.output_dir)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))

    print(f"Valid records: {cleaned}")
    print(f"Rejected records: {rejected}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()

