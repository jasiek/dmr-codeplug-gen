import sys

from codeplug import Codeplug
from generators import BrandmeisterTGContactGenerator, CountryGroupListGenerator

if __name__ == "__main__":
    Codeplug(BrandmeisterTGContactGenerator()).generate(sys.stdout)
