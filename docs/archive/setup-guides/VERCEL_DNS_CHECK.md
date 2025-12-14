# Vercel DNS 設定檢查指南

**域名**: lexicraft.xyz  
**日期**: January 2025

---

## 🔍 快速檢查步驟

### Step 1: 檢查 Vercel 域名設定

1. **前往 Vercel Dashboard**
   - 連結: https://vercel.com/dashboard
   - 選擇你的 **landing-page** 專案

2. **檢查域名狀態**
   - 前往: **Settings** → **Domains**
   - 查看 `lexicraft.xyz` 的狀態

### Step 2: 檢查域名狀態指示

在 Vercel Domains 頁面，你會看到以下狀態之一：

#### ✅ **Valid Configuration** (正確設定)
- 綠色勾號 ✓
- 表示 DNS 已正確設定
- SSL 證書已自動配置
- 域名應該可以正常訪問

#### ⚠️ **Invalid Configuration** (設定錯誤)
- 紅色警告 ⚠️
- 表示 DNS 記錄不正確
- 需要檢查 DNS 設定

#### 🔄 **Pending** (等待中)
- 黃色時鐘圖示
- DNS 正在傳播中
- 等待 5-60 分鐘

#### ❌ **Not Configured** (未設定)
- 灰色狀態
- 域名尚未添加到 Vercel
- 需要先添加域名

---

## 📋 詳細檢查清單

### 1. Vercel 域名設定檢查

- [ ] 域名已添加到 Vercel 專案
- [ ] 域名狀態顯示 "Valid Configuration"
- [ ] SSL 證書狀態為 "Valid" 或 "Provisioning"
- [ ] 沒有錯誤訊息

### 2. DNS 記錄檢查

#### 如果使用 Cloudflare:

**檢查 A 記錄 (根域名):**
```
Type: A
Name: @ (或空白)
Content: 76.76.21.21 (Vercel 的 IP)
Proxy: ✅ (橙色雲朵 - 啟用)
```

**檢查 CNAME 記錄 (www):**
```
Type: CNAME
Name: www
Target: cname.vercel-dns.com
Proxy: ✅ (橙色雲朵 - 啟用)
```

#### 如果使用其他 DNS 提供商:

Vercel 會顯示需要添加的 DNS 記錄，通常包括：
- A 記錄指向 Vercel IP
- CNAME 記錄指向 `cname.vercel-dns.com`

---

## 🔧 如何修復常見問題

### 問題 1: "Invalid Configuration"

**原因**: DNS 記錄不正確

**解決方法**:
1. 檢查 Cloudflare DNS 記錄是否正確
2. 確認 A 記錄指向正確的 Vercel IP
3. 確認 CNAME 記錄指向 `cname.vercel-dns.com`
4. 等待 5-10 分鐘讓 DNS 更新

### 問題 2: "Pending" 狀態很久

**原因**: DNS 傳播緩慢

**解決方法**:
1. 檢查 DNS 傳播狀態: https://dnschecker.org/#A/lexicraft.xyz
2. 確認 DNS 記錄已正確設定
3. 清除本地 DNS 快取
4. 等待最多 60 分鐘

### 問題 3: SSL 證書未配置

**原因**: DNS 未正確設定或仍在傳播

**解決方法**:
1. 確認 DNS 記錄正確
2. 等待 DNS 完全傳播
3. Vercel 會自動配置 SSL（5-10 分鐘）
4. 如果 1 小時後仍未配置，檢查 DNS 設定

---

## 🧪 測試域名設定

### 測試 1: 檢查域名解析

```bash
# 檢查 A 記錄
dig A lexicraft.xyz

# 應該返回 Vercel 的 IP 地址
# 例如: 76.76.21.21
```

### 測試 2: 檢查網站可訪問性

```bash
# 測試 HTTP 回應
curl -I https://lexicraft.xyz

# 應該返回:
# HTTP/2 200
# 或
# HTTP/1.1 301 (重定向到 HTTPS)
```

### 測試 3: 檢查 SSL 證書

```bash
# 檢查 SSL 證書
openssl s_client -connect lexicraft.xyz:443 -servername lexicraft.xyz

# 應該顯示有效的 SSL 證書
```

### 測試 4: 瀏覽器測試

1. 訪問: https://lexicraft.xyz
2. 檢查瀏覽器地址欄是否有鎖頭圖示 🔒
3. 確認網站正常載入
4. 檢查控制台是否有錯誤

---

## 📊 Vercel 域名狀態說明

| 狀態 | 圖示 | 說明 | 行動 |
|------|------|------|------|
| **Valid** | ✅ 綠色勾號 | DNS 正確，SSL 已配置 | 無需行動 |
| **Invalid** | ⚠️ 紅色警告 | DNS 設定錯誤 | 檢查 DNS 記錄 |
| **Pending** | 🔄 黃色時鐘 | DNS 傳播中 | 等待 5-60 分鐘 |
| **Not Configured** | ❌ 灰色 | 域名未添加 | 添加域名 |

---

## 🔗 有用的連結

### Vercel 相關
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Domains 文檔](https://vercel.com/docs/concepts/projects/domains)
- [Vercel DNS 設定指南](https://vercel.com/docs/concepts/projects/domains/add-a-domain)

### DNS 檢查工具
- [DNS Checker](https://dnschecker.org/#A/lexicraft.xyz)
- [WhatsMyDNS](https://www.whatsmydns.net/#A/lexicraft.xyz)
- [IntoDNS](https://intodns.com/lexicraft.xyz)

### Cloudflare
- [Cloudflare Dashboard](https://dash.cloudflare.com)
- [Cloudflare DNS 文檔](https://developers.cloudflare.com/dns/)

---

## 🎯 下一步行動

根據檢查結果：

### 如果狀態是 ✅ Valid:
1. ✅ 域名設定正確
2. ⏭️ 測試網站功能
3. ⏭️ 設定 API 子域名（如果需要）
4. ⏭️ 更新環境變數

### 如果狀態是 ⚠️ Invalid:
1. 🔧 檢查 DNS 記錄
2. 🔧 確認記錄指向正確的 Vercel IP
3. ⏳ 等待 DNS 更新
4. 🔄 重新檢查狀態

### 如果狀態是 🔄 Pending:
1. ⏳ 等待 5-60 分鐘
2. 🔍 使用 DNS 檢查工具確認傳播狀態
3. 🔄 定期重新檢查 Vercel 狀態

---

## 💡 提示

1. **DNS 傳播時間**: 通常 5-60 分鐘，但可能長達 24-48 小時
2. **SSL 證書**: Vercel 會自動配置，通常在 DNS 正確後 5-10 分鐘
3. **快取問題**: 如果本地無法訪問，清除 DNS 快取
4. **多個位置測試**: 使用 DNS 檢查工具從多個位置測試

---

## 📞 需要幫助？

如果遇到問題：
1. 檢查 Vercel 部署日誌
2. 檢查 Cloudflare DNS 記錄
3. 使用 DNS 檢查工具確認傳播狀態
4. 查看 Vercel 文檔或聯繫支援


