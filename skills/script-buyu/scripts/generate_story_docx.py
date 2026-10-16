"""Format an Agent-authored screenplay; this command does not write stories."""
import argparse
from story_contract import ContractError, read_json
from screenplay_docx import create_docx
from artifact_identity import artifact_purpose


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--purpose",choices=["auto","engineering","work_draft"],default="auto")
    args = parser.parse_args()
    try:
        story = read_json(args.input)
        purpose = artifact_purpose(args.input,story=story,declared=args.purpose)
        create_docx(story, args.output, artifact_purpose=purpose, source=args.input)
    except (ContractError, OSError, ValueError) as exc:
        parser.exit(2, f"Cannot export: {exc}\n")
    print("Engineering DOCX created; budget metadata only, not a creative deliverable." if purpose == "engineering" else "Work-draft DOCX created; awaiting content confirmation and layout review; duration is budget metadata only.")


if __name__ == "__main__":
    main()
