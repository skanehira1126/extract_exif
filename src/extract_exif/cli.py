import os
import argparse
import platform

import pandas as pd
from tqdm.auto import tqdm

from extract_exif.proc import read_image, to_fraction, extract_info


def get_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("file", nargs="+", help="処理するファイルのパス")

    return parser


def extract(file):
    exif_info_all = read_image(file)

    exif_info = extract_info(exif_info_all)
    # 露出時間を分数表記に変換
    try:
        exif_info["露出時間（分数）"] = to_fraction(float(exif_info["露出時間"]))
    except:
        exif_info["露出時間（分数）"] = "Not Found"

    exif_info["ファイルパス"] = file

    return exif_info


def cli():
    parser = get_parser()

    args = parser.parse_args()

    output_list = []
    for file in tqdm(args.file):
        if os.path.isdir(file):
            for name in os.listdir(file):
                if (
                    name.endswith(".jpeg")
                    or name.endswith(".jpg")
                    or name.endswith(".JPEG")
                    or name.endswith(".JPG")
                ):
                    file_path = os.path.join(file, name)
                    exif_info = extract(file_path)
                    exif_info["ファイル名"] = name
                    output_list.append(exif_info)
        elif (
            file.endswith(".jpeg")
            or file.endswith(".jpg")
            or file.endswith(".JPEG")
            or file.endswith(".JPG")
        ):
            exif_info = extract(file)
            exif_info["ファイル名"] = os.path.basename(file)
            output_list.append(exif_info)
        else:
            continue

    if platform.system() == "Windows":
        encode = "shift-jis"
    else:
        encode = "utf-8"

    df_exif_info = pd.DataFrame(output_list).set_index("ファイル名")
    # 並び替え
    backward_columns = ["ファイルパス"]
    df_exif_info = df_exif_info[
        [col for col in df_exif_info.columns if col not in backward_columns]
        + [col for col in df_exif_info.columns if col in backward_columns]
    ]
    df_exif_info.sort_index().to_csv(
        "写真情報.csv",
        encoding=encode,
    )
