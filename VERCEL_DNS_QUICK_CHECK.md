# Vercel DNS 快速檢查清單

**域名**: lexicraft.xyz

---

## 🚨 目前狀態

根據 DNS 查詢結果：
- ❌ 域名尚未解析（DNS 記錄可能未設定或未傳播）

---

## ✅ 立即檢查步驟

### 1. 檢查 Vercel 域名設定

**前往**: https://vercel.com/dashboard

1. 選擇你的專案（landing-page）
2. 前往 **Settings** → **Domains**
3. 查看是否有 `lexicraft.xyz`

**如果沒有域名**:
- 點擊 **"Add Domain"**
- 輸入: `lexicraft.xyz`
- 點擊 **"Add"**
- Vercel 會顯示需要添加的 DNS 記錄

**如果有域名，檢查狀態**:
- ✅ **Valid Configuration** = 正確設定
- ⚠️ **Invalid Configuration** = 需要修復 DNS
- 🔄 **Pending** = 等待 DNS 傳播

---

### 2. 檢查 Cloudflare DNS 記錄

**前往**: https://dash.cloudflare.com

1. 選擇 `lexicraft.xyz`
2. 前往 **DNS** → **Records**
3. 檢查是否有以下記錄：

#### 必須的記錄：

**A 記錄 (根域名)**:
```
Type: A
Name: @ (或空白)
IPv4 address: [Vercel 提供的 IP，通常是 76.76.21.21]
Proxy status: ✅ Proxied (橙色雲朵)
```

**CNAME 記錄 (www)**:
```
Type: CNAME
Name: www
Target: cname.vercel-dns.com
Proxy status: ✅ Proxied (橙色雲朵)
```

---

### 3. 如果沒有 DNS 記錄，添加它們

#### 在 Cloudflare 添加 A 記錄：

1. 點擊 **"Add record"**
2. 選擇 **Type: A**
3. **Name**: `@` (或留空)
4. **IPv4 address**: 從 Vercel 複製的 IP 地址
5. **Proxy status**: ✅ **Proxied** (橙色雲朵)
6. 點擊 **"Save"**

#### 在 Cloudflare 添加 CNAME 記錄：

1. 點擊 **"Add record"**
2. 選擇 **Type: CNAME**
3. **Name**: `www`
4. **Target**: `cname.vercel-dns.com`
5. **Proxy status**: ✅ **Proxied** (橙色雲朵)
6. 點擊 **"Save"**

---

## 🔍 如何獲取 Vercel 的 DNS 記錄

### 方法 1: 從 Vercel Dashboard

1. 前往 Vercel → Settings → Domains
2. 點擊 `lexicraft.xyz`
3. 查看 **"Configuration"** 區塊
4. 複製顯示的 DNS 記錄

### 方法 2: Vercel 自動顯示

當你添加域名時，Vercel 會自動顯示需要添加的 DNS 記錄。

---

## ⏱️ 等待 DNS 傳播

添加 DNS 記錄後：

1. **等待 5-60 分鐘** 讓 DNS 傳播
2. **檢查傳播狀態**: https://dnschecker.org/#A/lexicraft.xyz
3. **檢查 Vercel 狀態**: 返回 Vercel Dashboard 查看域名狀態

---

## 🧪 測試命令

### 檢查 DNS 解析：
```bash
# 檢查 A 記錄
dig A lexicraft.xyz +short

# 應該返回 Vercel 的 IP 地址
# 例如: 76.76.21.21
```

### 檢查網站可訪問性：
```bash
# 測試 HTTPS
curl -I https://lexicraft.xyz

# 如果成功，應該返回 HTTP/2 200
```

---

## 📋 完整檢查清單

- [ ] 域名已添加到 Vercel
- [ ] Vercel 顯示 DNS 記錄需求
- [ ] A 記錄已添加到 Cloudflare
- [ ] CNAME 記錄已添加到 Cloudflare
- [ ] 所有記錄的 Proxy 狀態為 ✅ Proxied
- [ ] 等待 5-60 分鐘
- [ ] DNS 傳播檢查工具顯示綠色
- [ ] Vercel 狀態顯示 "Valid Configuration"
- [ ] SSL 證書已配置
- [ ] 網站可以訪問 https://lexicraft.xyz

---

## 🆘 常見問題

### Q: Vercel 顯示 "Invalid Configuration"
**A**: 檢查 DNS 記錄是否正確，確認 IP 地址和 CNAME 目標正確

### Q: DNS 記錄已添加但還是無效
**A**: 等待 5-60 分鐘讓 DNS 傳播，使用 DNS 檢查工具確認

### Q: 如何知道 Vercel 的 IP 地址？
**A**: 在 Vercel Dashboard → Settings → Domains → 點擊域名，會顯示需要的 DNS 記錄

### Q: Proxy 狀態應該選什麼？
**A**: 對於 Vercel，使用 ✅ **Proxied** (橙色雲朵)，這樣可以使用 Cloudflare 的 CDN

---

## 🔗 快速連結

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Cloudflare Dashboard](https://dash.cloudflare.com)
- [DNS Checker](https://dnschecker.org/#A/lexicraft.xyz)
- [Vercel Domains 文檔](https://vercel.com/docs/concepts/projects/domains)

---

## 💡 下一步

1. **現在**: 檢查 Vercel 是否有域名設定
2. **如果沒有**: 添加域名並獲取 DNS 記錄
3. **如果有**: 檢查狀態並修復任何問題
4. **添加 DNS 記錄**: 在 Cloudflare 添加 Vercel 提供的記錄
5. **等待**: 5-60 分鐘讓 DNS 傳播
6. **驗證**: 使用 DNS 檢查工具和測試命令


