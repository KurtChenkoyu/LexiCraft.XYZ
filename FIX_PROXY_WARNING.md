# 修復 Vercel "Proxy Detected" 警告

**問題**: Cloudflare Proxy 阻止 Vercel 的自動 DDoS 和 bot-mitigation 工具

---

## 🔧 解決方案：禁用 Cloudflare Proxy

### 步驟 1: 前往 Cloudflare Dashboard

1. 打開: https://dash.cloudflare.com
2. 選擇域名: `lexicraft.xyz`
3. 前往: **DNS** → **Records**

### 步驟 2: 修改 DNS 記錄

找到以下記錄並將 Proxy 狀態改為 **DNS only**（灰色雲朵）：

#### 記錄 1: 根域名 A 記錄
```
Type: A
Name: @ (或空白)
IPv4 address: [保持不變]
Proxy status: ❌ DNS only (灰色雲朵) ← 改這個
```

#### 記錄 2: www CNAME 記錄
```
Type: CNAME
Name: www
Target: cname.vercel-dns.com
Proxy status: ❌ DNS only (灰色雲朵) ← 改這個
```

### 步驟 3: 等待更新

- DNS 更新需要 5-10 分鐘
- Vercel 會自動偵測變化
- 警告應該會自動消失

---

## ✅ 驗證修復

### 在 Vercel Dashboard 檢查：

1. 返回 Vercel → Settings → Domains
2. 檢查 `lexicraft.xyz` 和 `www.lexicraft.xyz`
3. "Proxy Detected" 警告應該消失
4. 狀態應該顯示 "Valid Configuration"

### 測試網站：

```bash
# 測試根域名
curl -I https://lexicraft.xyz

# 測試 www 子域名
curl -I https://www.lexicraft.xyz

# 應該都返回 HTTP/2 200
```

---

## 📝 為什麼要禁用 Proxy？

### Cloudflare Proxy 的問題：

1. **阻止 Vercel 的 DDoS 防護**: Vercel 無法看到真實 IP
2. **降低性能**: 額外的代理層增加延遲
3. **Bot 檢測失效**: Vercel 的 bot-mitigation 工具無法正常工作
4. **分析數據不準確**: 流量統計可能不準確

### DNS Only 的好處：

1. ✅ Vercel 可以正常運作所有功能
2. ✅ 更好的性能（減少代理層）
3. ✅ 準確的分析數據
4. ✅ 完整的 DDoS 防護

**注意**: 你仍然可以使用 Cloudflare 的其他功能（DNS 管理、其他子域名等），只是根域名和 www 不使用 proxy。

---

## 🎯 完成後的狀態

修復後，Vercel Dashboard 應該顯示：

- ✅ `lexicraft.xyz` - Valid Configuration（無警告）
- ✅ `www.lexicraft.xyz` - Valid Configuration（無警告）
- ✅ SSL 證書正常
- ✅ 網站可以正常訪問

---

## 💡 提示

- **其他子域名**: 如果未來需要 `api.lexicraft.xyz` 等子域名，也應該使用 DNS only（不 proxy）
- **Cloudflare 其他功能**: 你仍然可以使用 Cloudflare 的 DNS 管理、其他安全功能等
- **Vercel 的保護**: Vercel 本身就有很好的 DDoS 防護，不需要 Cloudflare Proxy


