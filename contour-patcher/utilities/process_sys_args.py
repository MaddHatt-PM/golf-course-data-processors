import os
import sys
from pathlib import Path


def process_sys_args() -> tuple[Path, Path]:
    """
    It takes in a path to an image, and returns a path to the image and a path to the output image.
    Return the input and output path as a tuple
    """
    if len(sys.argv) < 2:
        print("Not enough arguements")
        print("python run.py <target-img-path> <opt-output-path>")
        sys.exit(0)

    try:
        inpath = Path(sys.argv[1])
    except:
        print("Invalid target path")
        sys.exit(0)

    if len(sys.argv) < 3:
        try:
            outpath = Path(sys.argv[2])
        except:
            print("Invalid output path")
            sys.exit(0)

    else:
        outpath = Path.joinpath(inpath.parent, inpath.stem + "_result" + inpath.suffix)

    return inpath, outpath
