"""Read edited, visible screenplay content into internal working data."""
import argparse
from story_contract import ContractError, write_json_new
from screenplay_docx import extract_docx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        write_json_new(args.output, extract_docx(args.input))
    except (ContractError, OSError, ValueError) as exc:
        parser.exit(2, f"Cannot import: {exc}\n")
    print("Visible screenplay extracted; no approval or production stage was started.")


if __name__ == "__main__":
    main()
