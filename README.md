# DigiKey 產品搜尋腳本

這是一個簡單的 Python 腳本，從 DigiKey 取得臨時 OAuth2 令牌，並使用 DigiKey API 執行關鍵字產品搜尋。

## 系統需求

- Python 3.7+
- `requests`
- `python-dotenv`

## 設定

1. 安裝相依套件：

```bash
pip install requests python-dotenv
```

2. 在相同資料夾中建立 `.env` 檔案，內容如下：

```env
CLIENT_ID=your_digikey_client_id
CLIENT_SECRET=your_digikey_client_secret
```

## 使用方式

在專案資料夾中執行腳本：

```bash
python main.py
```

此腳本將會：

- 從 `.env` 載入 API 憑證
- 向 DigiKey 請求 OAuth2 存取令牌
- 使用 DigiKey 產品搜尋 API 執行關鍵字搜尋
- 列印分類名稱、子分類、封裝/外殼和供應商器件封裝資訊

## 注意事項

- 目前的搜尋關鍵字可透過命令列參數傳入。
- 若要搜尋，請使用 `python main.py <keywords> [recordLimit = 5]`。

- 腳本會根據設定的 URL 使用 DigiKey 沙盒或正式環境端點。
