import os
import argparse
import platform

import pandas as pd

from extract_exif.reader import read_image, extract_info


def get_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("file", nargs="+", help="処理するファイルのパス")

    return parser


def cli():
    parser = get_parser()

    args = parser.parse_args()

    output_dict = {}
    for file in args.file:

        exif_info_all = read_image(file)

        output_dict[os.path.basename(file)] = extract_info(exif_info_all)

    if platform.system() == "Windows":
        encode = "shift-jis"
    else:
        encode = "utf-8"

    pd.DataFrame(output_dict).T.sort_index().to_csv(
        "jpeg_infomations.csv",
        encoding=encode,
    )
