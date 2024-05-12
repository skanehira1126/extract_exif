import base64
import io
import platform
import zipfile

import pandas as pd
import streamlit as st
from PIL import Image

from extract_exif.proc import extract_info
from extract_exif.proc import to_fraction

st.set_page_config(
    layout="wide",
)


# 初期化設定
def initialize():
    if "default_encoding" not in st.session_state:
        st.session_state.default_encoding = (
            "shift-jis" if platform.system() == "Windows" else "utf-8"
        )

    if "current_images" not in st.session_state:
        st.session_state.current_images = []

    if "selected_images" not in st.session_state:
        st.session_state.selected_images = []


def file_preview():
    uploaded_files = st.file_uploader(
        "対象のファイルもしくはディレクトリ",
        accept_multiple_files=True,
    )
    if len(uploaded_files) >= 1:
        image_files = []
        for _file in uploaded_files:
            raw_image = _file.getvalue()
            image = Image.open(io.BytesIO(raw_image))

            # タグの取得
            exif_info_all = image.getexif()

            # 必要な情報を抽出
            extracted_info = extract_info(exif_info_all)
            extracted_info["露出時間"] = to_fraction(extracted_info["露出時間"])
            image_files.append(
                {
                    "image": image,
                    "raw_image": raw_image,
                    "file_id": _file.file_id,
                    "name": _file.name,
                }
                | extracted_info
            )
        return sorted(image_files, key=lambda x: x["name"])

    return []


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
    image_bytes = io.BytesIO()
    image.save(
        image_bytes,
        optimize=True,
        quality=compression_rate,
        format=image.format,
    )

    return image_bytes.getvalue()


def make_image_df(image_files):
    image_df = pd.DataFrame(
        [
            {
                "プレビュー": f"data:image/jpg;base64,{base64.b64encode(get_compressed_image_bytes(img['image'])).decode()}",
                "file_id": img["file_id"],
                "ファイル名": img["name"],
                "露出時間": img["露出時間"],
                "ISO感度": img["ISO感度"],
                "焦点距離": img["焦点距離"],
                "F値": img["F値"],
                "選択": img["file_id"] in st.session_state.selected_images,
            }
            for img in image_files
        ]
    ).drop_duplicates(["プレビュー"], keep="first")

    return image_df


def get_binary_of_images(uploaded_files):
    bytes_io = io.BytesIO()

    with zipfile.ZipFile(bytes_io, "w") as zipf:
        for file in filter(
            lambda x: x["file_id"] in st.session_state.selected_images, uploaded_files
        ):
            zipf.writestr(file["name"], file["raw_image"])

    bytes_io.seek(0)

    return bytes_io.getvalue()


initialize()
# アップロードしたファイルのpreview
image_files = file_preview()

update_images = set(st.session_state.current_images) != set(
    [img["file_id"] for img in image_files]
)

st.session_state.current_images = [img["file_id"] for img in image_files]


if len(image_files) >= 1:
    if st.button("全選択"):
        st.session_state.image_df["選択"] = True
    if update_images:
        st.session_state.image_df = make_image_df(image_files)

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
            "露出時間",
            "ISO感度",
            "焦点距離",
            "F値",
        ],
        hide_index=True,
        height=250,
        use_container_width=True,
    )

    st.session_state.selected_images = [
        file_id for file_id in output_df[output_df["選択"]]["file_id"].values
    ]

st.download_button(
    "選択した画像のみダウンロード",
    data=get_binary_of_images(uploaded_files=image_files),
    file_name="images.zip",
    mime="application/zip",
    disabled=len(st.session_state.selected_images) == 0,
    help="選択列で画像を選択してください",
)


if st.session_state.selected_images:
    n_images = len(st.session_state.selected_images)
    for row_idx in range(n_images // 3 + (n_images % 3 > 0)):
        cols = st.columns(3)
        imgs = st.session_state.selected_images[row_idx * 3 : row_idx * 3 + 3]

        for col, _img in zip(cols, imgs):
            _img = list(filter(lambda x: x["file_id"] == _img, image_files))[0]
            with col:
                st.markdown(f"#### {_img['name']}", help=get_caption(_img))
                st.image(_img["image"], caption=get_caption(_img))

    st.divider()
