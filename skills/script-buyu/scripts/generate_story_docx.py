"""Format an Agent-authored screenplay; this command does not write stories."""
import argparse
from story_contract import ContractError, read_json
from screenplay_docx import create_docx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        create_docx(read_json(args.input), args.output)
    except (ContractError, OSError, ValueError) as exc:
        parser.exit(2, f"Cannot export: {exc}\n")
    print("DOCX created; awaiting content confirmation and visual layout review.")


if __name__ == "__main__":
    main()
