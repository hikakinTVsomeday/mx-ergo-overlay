# MX Ergo S ジェスチャー・チートシート・オーバーレイ

MX Ergo S のジェスチャーボタンを押している間、現在アクティブなアプリケーションに応じたジェスチャーアクションのチートシートを画面にオーバーレイ表示する Windows 常駐アプリです。

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの編集

`config.json` を開き、自分の Logi Options+ のジェスチャー設定に合わせて編集してください。

```json
{
  "trigger_button": "middle",
  "apps": {
    "chrome.exe": {
      "app_name": "Google Chrome",
      "up": "新しいタブ",
      "down": "タブを閉じる",
      "left": "戻る",
      "right": "進む"
    },
    "default": {
      "app_name": "Global",
      "up": "タスクビュー",
      "down": "デスクトップ表示",
      "left": "戻る",
      "right": "進む"
    }
  }
}
```

- **`trigger_button`**: `"middle"` (中ボタン), `"x1"` (拡張ボタン1), `"x2"` (拡張ボタン2) のいずれか
- **`apps`**: キーは実行ファイル名 (小文字)。`"default"` はどのアプリにも該当しない場合のフォールバック

### 3. Logi Options+ の設定

MX Ergo S の Logi Options+ で、ジェスチャーボタンの割り当てを `trigger_button` で指定したボタンに変更してください。

例: ジェスチャーボタン → ミドルクリック

## 起動

```bash
python main.py
```

- システムトレイにアイコンが表示されます
- トリガーボタンを**押している間**、アクティブアプリに応じたチートシートがマウスカーソル付近に表示されます
- ボタンを**離す**と非表示になります

## システムトレイメニュー

- **設定を再読み込み**: `config.json` の変更を反映
- **終了**: アプリを終了
