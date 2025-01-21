import base64
import io
import platform
import zipfile
from dataclasses import dataclass
from logging import Formatter, StreamHandler, getLogger

import pandas as pd
import streamlit as st
from PIL import Image

from extract_exif.proc import extract_info, to_fraction

resize_method_list = [
    "NEAREST",
    "BOX",
    "BILINEAR",
    "HAMMING",
    "BICUBIC",
    "LANCZOS",
]


logger = getLogger(__name__)
fmt = Formatter(
    "[%(levelname)s] %(name)s %(asctime)s - %(filename)s: %(lineno)d: %(message)s",
)
sh = StreamHandler()
sh.setLevel("DEBUG")
sh.setFormatter(fmt)
logger.addHandler(sh)


@dataclass
class IsDownloadEnable:
    is_enable: bool = False

    def disable(self):
        self.is_enable = False

    def enable(self):
        self.is_enable = True


st.set_page_config(
    layout="wide",
)


# 初期化設定
def initialize():
    """
    session_stateの初期化をする
    """
    if "default_encoding" not in st.session_state:
        st.session_state.default_encoding = (
            "shift-jis" if platform.system() == "Windows" else "utf-8"
        )

    if "current_images" not in st.session_state:
        st.session_state.current_images = []

    if "selected_image_file_ids" not in st.session_state:
        st.session_state.selected_image_file_ids = []

    if "download_images" not in st.session_state:
        st.session_state.download_images = b""

    if "is_download_enable" not in st.session_state:
        st.session_state.is_download_enable = IsDownloadEnable()


def extract_exif_of_uploaded_files():
    """
    Uploadした画像を読み込みDataFrameとして管理する
    """
    # ファイルの読み込み
    uploaded_files = st.file_uploader(
        "対象のファイルもしくはディレクトリ",
        accept_multiple_files=True,
    )

    # 読み込んだ画像の処理
    image_files = []
    if len(uploaded_files) >= 1:
        for _file in uploaded_files:
            raw_image = _file.getvalue()
            image = Image.open(io.BytesIO(raw_image))

            image_info = {
                "image": image,
                "raw_image": raw_image,
                "file_id": _file.file_id,
                "name": _file.name,
            }

            # jpegで情報がある場合
            try:
                # タグの取得
                exif_info_all = image.getexif()

                # 必要な情報を抽出
                extracted_info = extract_info(exif_info_all)
                extracted_info["露出時間"] = to_fraction(extracted_info["露出時間"])
                image_info.update(extracted_info)
            except Exception as _:
                logger.warning(
                    f"{_file.name} is not jpeg or does not have exif informations."
                )

            image_files.append(image_info)

    return sorted(image_files, key=lambda x: x["name"])


def get_caption(
    img_info,
):
    return (
        f"露出時間: {img_info['露出時間']} "
        f"ISO感度: {img_info['ISO感度']} "
        f"焦点距離: {img_info['焦点距離']} "
        f"F値: {img_info['F値']}"
    )


def get_compressed_image_bytes(image, compression_rate=10):
    """
    画像を圧縮してのbyteを取得する
    """
    image_bytes = io.BytesIO()
    image.save(
        image_bytes,
        optimize=True,
        quality=compression_rate,
        format=image.format,
    )

    return image_bytes.getvalue()


def make_image_df(image_files):
    """
    読み込んだ画像を一元管理するためのDataFrameを表示する
    """
    image_df = pd.DataFrame(
        [
            {
                "プレビュー": f"data:image/jpg;base64,{base64.b64encode(get_compressed_image_bytes(img['image'])).decode()}",
                "file_id": img["file_id"],
                "ファイル名": img["name"],
                "ファイルサイズ": img["image"].size[::-1],
                "露出時間": img["露出時間"],
                "ISO感度": img["ISO感度"],
                "焦点距離": int(img["焦点距離"]),
                "F値": img["F値"],
                "選択": img["file_id"] in st.session_state.selected_image_file_ids,
            }
            for img in image_files
        ]
    ).drop_duplicates(["プレビュー"], keep="first")

    return image_df


def get_bytes_of_images(uploaded_files, resize_ratio: float, resize_method: str):
    bytes_io = io.BytesIO()

    with zipfile.ZipFile(bytes_io, "w") as zipf:
        for file in filter(
            lambda x: x["file_id"] in st.session_state.selected_image_file_ids,
            uploaded_files,
        ):
            img = file["image"]
            new_size = int(img.size[0] * resize_ratio), int(img.size[1] * resize_ratio)
            img_bytes = io.BytesIO()
            file["image"].resize(new_size, getattr(Image, resize_method)).save(
                img_bytes, format="JPEG"
            )
            zipf.writestr(file["name"], img_bytes.getvalue())

    bytes_io.seek(0)

    return bytes_io.getvalue()


##########
#
# 初期化
#
##########
initialize()


##########
#
# ファイル読み込み
#
##########
# アップロードしたファイルのpreview
image_files = extract_exif_of_uploaded_files()
is_update_images = set(st.session_state.current_images) != set(
    [img["file_id"] for img in image_files]
)
st.session_state.current_images = [img["file_id"] for img in image_files]

if len(image_files) == 0:
    st.stop()

if is_update_images:
    st.session_state.image_df = make_image_df(image_files)

##########
#
# サムネイルと画像の情報を表示
#
##########

# DataFrameの状態に合わせてbuttonの挙動を変える
if st.session_state.image_df["選択"].all():
    button_text = "選択解除"
    check_box_value = False
else:
    button_text = "全選択"
    check_box_value = True

if st.button(button_text):
    st.session_state.image_df["選択"] = check_box_value
    st.rerun()


output_df = st.data_editor(
    st.session_state.image_df,
    column_config={
        "file_id": None,
        "プレビュー": st.column_config.ImageColumn(),
        "選択": st.column_config.CheckboxColumn(),
    },
    disabled=[col for col in st.session_state.image_df.columns if col != "選択"],
    column_order=[
        "選択",
        "プレビュー",
        "ファイル名",
        "ファイルサイズ",
        "露出時間",
        "ISO感度",
        "焦点距離",
        "F値",
    ],
    hide_index=True,
    height=250,
    use_container_width=True,
    on_change=lambda: st.session_state.is_download_enable.disable(),
)
st.session_state.selected_image_file_ids = [
    file_id for file_id in output_df[output_df["選択"]]["file_id"].values
]


##########
#
# 画像のPreviewを表示
#
##########
n_images = len(st.session_state.selected_image_file_ids)
if n_images:
    for row_idx in range(n_images // 3 + (n_images % 3 > 0)):
        cols = st.columns(3)
        imgs = st.session_state.selected_image_file_ids[row_idx * 3 : row_idx * 3 + 3]

        for col, _img in zip(cols, imgs):
            _img = list(filter(lambda x: x["file_id"] == _img, image_files))[0]
            with col:
                st.markdown(f"#### {_img['name']}", help=get_caption(_img))
                st.image(_img["image"], caption=get_caption(_img))

    st.divider()

##########
#
# 画像を縮小してダウンロード
#
##########
with st.form("画像のリサイズ"):
    resize_ratio = st.slider(
        "画像比率",
        min_value=0.05,
        max_value=1.0,
        step=0.01,
        value=0.33,
        help="高さと幅をそれぞれ比率に変更する",
    )
    resize_method = st.select_slider(
        "画像をリサイズする方法",
        options=resize_method_list,
        help="右に行く程高品質だが時間がかかる",
    )

    is_submit = st.form_submit_button(
        "リサイズ",
        disabled=len(st.session_state.selected_image_file_ids) == 0,
    )
if is_submit:
    with st.spinner("変換中"):
        st.session_state.download_images = get_bytes_of_images(
            uploaded_files=image_files,
            resize_ratio=resize_ratio,
            resize_method=resize_method,
        )
    st.session_state.is_download_enable.enable()

st.download_button(
    "リサイズした画像のダウンロード",
    data=st.session_state.download_images,
    file_name="images.zip",
    mime="application/zip",
    disabled=(
        len(st.session_state.download_images) == 0
        or not st.session_state.is_download_enable.is_enable
    ),
    help="選択列で画像を選択してください",
)
