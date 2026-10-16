"""Select a work draft or record source lineage; does not approve content."""
import argparse
from pathlib import Path
from artifact_identity import artifact_purpose, write_receipt, receipt_path, sha
from story_contract import ContractError, require, read_json, write_json_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True)
    parser.add_argument("--source",help="Actual source for an external artifact/derived XLSX")
    parser.add_argument("--source-purpose",choices=["auto","engineering","work_draft"],default="auto")
    parser.add_argument("--output",required=True,help="New selection record; never overwrites an old record")
    parser.add_argument("--record-only",action="store_true",help="Bind purpose to a derived artifact without selecting it for delivery")
    args = parser.parse_args()
    try:
        existing = receipt_path(args.input)
        if existing.exists():
            record = read_json(existing)
            require(record.get("artifact_sha256") == sha(args.input),
                "identity sidecar is stale for current bytes; retained recorded purpose="+str(record.get("purpose", "unknown"))+". Save the artifact to a new output path, then bind it with its actual source; the old record is not overwritten.")
        purpose = artifact_purpose(args.input)
        if args.source:
            source_purpose = artifact_purpose(args.source,declared=args.source_purpose)
            purpose = "engineering" if "engineering" in (purpose,source_purpose) else source_purpose
            require(purpose != "unknown", "source purpose is unknown; identify actual source before selecting")
            if not receipt_path(args.input).exists():
                write_receipt(args.input,purpose,source=args.source,source_purpose=source_purpose)
        require(args.record_only or purpose == "work_draft", "not a work draft: "+purpose+"; engineering/unknown artifacts cannot enter user-work delivery")
        write_json_new(args.output,{"artifact":str(Path(args.input).resolve()),"artifact_sha256":sha(args.input),
            "purpose":purpose,"selection":"identity_record_only" if args.record_only else "work_draft_for_review",
            "content_confirmation":"not_granted","layout_review":"not_certified","runtime":"not_measured"})
    except (ContractError,OSError,ValueError) as exc:
        parser.exit(2,f"Cannot select: {exc}\n")
    print("Identity recorded only; not a work delivery." if args.record_only else "Work draft selected for review; content/layout/timing are not certified.")


if __name__ == "__main__":
    main()
