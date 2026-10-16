"""Read edited, visible screenplay content into internal working data."""
import argparse
from story_contract import ContractError, write_json_new
from screenplay_docx import extract_docx
from artifact_identity import artifact_purpose, receipt_path, write_receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        story = extract_docx(args.input)
        purpose = artifact_purpose(args.input,story=story)
        if receipt_path(args.output).exists():
            raise ContractError("identity sidecar already exists; use a new output path")
        write_json_new(args.output,story)
        write_receipt(args.output,purpose,source=args.input,story=story)
    except (ContractError, OSError, ValueError) as exc:
        parser.exit(2, f"Cannot import: {exc}\n")
    print("Visible screenplay extracted; purpose="+purpose+"; no approval or production stage was started.")


if __name__ == "__main__":
    main()
