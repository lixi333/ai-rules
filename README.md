# ai-rules

精选 AI 服务分流规则订阅（自动合并、每日更新）。

## 规则来源

[VPSDance/ai-proxy-rules](https://github.com/VPSDance/ai-proxy-rules) 按服务精选的热门 AI 服务：
OpenAI、Anthropic、Google、DeepSeek、Cursor、Copilot、Perplexity、
Midjourney、Groq、Poe、OpenRouter、Mistral、Moonshot（Kimi）、Qwen（通义），
另手动补充 Grok（VPSDance 未收录）。

与 [muse-rules](https://github.com/lixi333/muse-rules) 重叠的 6 个 Meta AI 域名
（`atmeta.com`、`llama.com`、`llamameta.net`、`meta.ai`、`metaaivm.com`、`muse.ai`）
已剔除，两个规则集零重叠，可指向不同节点。

GitHub Actions 每天 02:00 UTC 自动抓取、合并去重后提交，
`AI-merged.list` 和 `AI.arrs` 永远是最新版。

## 订阅方式

### Anywhere（iOS）

把下面任一 URL 加为远程规则集（`.arrs` 为 Anywhere 专用格式），
导入后手动把该规则集指向你的代理策略组：

- GitHub Raw：`https://raw.githubusercontent.com/lixi333/ai-rules/main/AI.arrs`
- jsDelivr CDN（国内访问更快）：`https://cdn.jsdelivr.net/gh/lixi333/ai-rules@main/AI.arrs`

### Loon / Surge（通用格式）

把下面任一 URL 加为远程规则集：

- GitHub Raw：`https://raw.githubusercontent.com/lixi333/ai-rules/main/AI-merged.list`
- jsDelivr CDN（国内访问更快）：`https://cdn.jsdelivr.net/gh/lixi333/ai-rules@main/AI-merged.list`

## 说明

- Anywhere 不支持精确域名匹配，`DOMAIN` 类型已按官方转换做法转为域名后缀规则。
- `PROCESS-NAME`、`IP-ASN` 等 Anywhere 不支持的类型在转换时跳过（数量见文件头部的 `SKIPPED` 注释）。
