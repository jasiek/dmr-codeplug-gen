import importlib
import sys
import argparse

from anytone import AT878UV
from writers import QDMRWriter

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DMR codeplug")
    parser.add_argument("filename", help="Output file name")
    parser.add_argument("callsign", help="Callsign")
    parser.add_argument("dmr_id", type=int, help="DMR ID")
    parser.add_argument("recipe", help="Recipe name")
    parser.add_argument("timezone", nargs="?", default=None, help="Timezone (optional)")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to show filtered records",
    )

    args = parser.parse_args()

    recipe_class = importlib.import_module(f"recipes.{args.recipe}").Recipe
    recipe_class(
        args.callsign,
        args.dmr_id,
        args.filename,
        AT878UV,
        QDMRWriter,
        args.timezone,
        debug=args.debug,
    ).generate()
