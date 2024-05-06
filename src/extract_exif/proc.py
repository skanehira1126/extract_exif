from fractions import Fraction

from PIL import Image


def read_image(file_path: str) -> Image.Exif:

    with Image.open(file_path) as im:
        exif_info_all = im.getexif()

    return exif_info_all


def extract_info(exif_info_all: Image.Exif) -> dict:
    """
    Exif情報から必要な情報を引き出す。
    見つからない場合はUnknownを返却する
    """

    # 必要なExif情報を取得
    # 他にはGPS情報とかもある
    exif_tags = exif_info_all.get_ifd(34665)

    # 取得するTagと名前
    tag_name_map = {
        0x829A: "露出時間",
        0x8827: "ISO感度",
        0x920A: "焦点距離",
        0x829D: "F値",
    }

    extracted_info = {name: exif_tags.get(tag, "Not Found") for tag, name in tag_name_map.items()}

    return extracted_info


def to_fraction(decimal, max_denominator=5000) -> str:
    """
    浮動小数点の数値を適当な分数表記に変換する.
    """
    # 分数
    frac = Fraction(decimal)

    # 適当な分数に変換
    frac_str = str(frac.limit_denominator(max_denominator))

    return frac_str
