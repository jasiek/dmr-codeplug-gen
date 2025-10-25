import importlib
import sys

from anytone import AT878UV
from writers import QDMRWriter

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("missing output file name")
        exit(1)

    if len(sys.argv) < 3:
        print("missing callsign")
        exit(1)

    if len(sys.argv) < 4:
        print("missing dmr_id")
        exit(1)

    if len(sys.argv) < 5:
        print("missing recipe")
        exit(1)

    filename = sys.argv[1]
    callsign = sys.argv[2]
    dmr_id = int(sys.argv[3])
    recipe_name = sys.argv[4]

    recipe_class = importlib.import_module(f"recipes.{recipe_name}").Recipe
    recipe_class(callsign, dmr_id, filename, AT878UV, QDMRWriter).generate()
