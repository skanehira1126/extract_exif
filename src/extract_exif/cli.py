import os
import argparse
import platform

import pandas as pd

from extract_exif.proc import read_image, to_fraction, extract_info


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

        exif_info = extract_info(exif_info_all)
        # 露出時間を分数表記に変換
        try:
            exif_info["露出時間（分数）"] = to_fraction(float(exif_info["露出時間"]))
        except:
            exif_info["露出時間（分数）"] = "Not Found"

        output_dict[os.path.basename(file)] = exif_info

    if platform.system() == "Windows":
        encode = "shift-jis"
    else:
        encode = "utf-8"

    pd.DataFrame(output_dict).T.sort_index().to_csv(
        "写真情報.csv",
        encoding=encode,
    )
