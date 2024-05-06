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
