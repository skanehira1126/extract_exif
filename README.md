# extract_exif

## 概要
jpeg画像から情報を抜き出してcsvに書き出すスクリプト

抽出情報

- 露出時間（分数 / 少数）
- F値
- ISO感度
- 焦点距離

## 環境構築

1. ryeのinstall
2. gitのinstall
3. パッケージのインストール: `rye install extract_exif --git https://github.com/skanehira1126/extract_exif`
4. 実行用batファイルの作成

```
@echo off
extract-exif %*
```

