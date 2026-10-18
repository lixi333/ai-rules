#!/usr/bin/env python3
"""Fetch, merge and dedupe curated popular AI service rule lists.

Sources (VPSDance/ai-proxy-rules, per-service lists):
  openai, anthropic, google-ai, deepseek, cursor, copilot, perplexity,
  midjourney, groq, poe, openrouter, mistral-ai, moonshot-ai, alibaba-ai (Qwen)
Plus manual Grok domains (VPSDance has no grok/xai list).

Outputs (repo root):
  - AI-merged.list : Loon/Surge 通用格式
  - AI.arrs        : Anywhere 专用格式

Excluded: 6 Meta AI domains that overlap with the muse-rules repo
(atmeta.com, llama.com, llamameta.net, meta.ai, metaaivm.com, muse.ai)
so the two rule sets can point to different nodes without ambiguity.

Anywhere rule types: 0=IPv4 CIDR, 1=IPv6 CIDR, 2=domain suffix, 3=keyword.
Anywhere has no exact-domain match, so DOMAIN entries are emitted as
suffix rules (same as the official anywhere-rules converter does).
PROCESS-NAME / IP-ASN have no Anywhere equivalent and are skipped.
"""
import datetime
import sys
import urllib.request

BASE = "https://cdn.jsdelivr.net/gh/VPSDance/ai-proxy-rules@main/rules/loon"

SERVICES = [
    "openai",       # OpenAI / ChatGPT
    "anthropic",    # Claude
    "google-ai",    # Gemini
    "deepseek",     # DeepSeek
    "cursor",       # Cursor
    "copilot",      # GitHub Copilot
    "perplexity",   # Perplexity
    "midjourney",   # Midjourney
    "groq",         # Groq
    "poe",          # Poe
    "openrouter",   # OpenRouter
    "mistral-ai",   # Mistral
    "moonshot-ai",  # Moonshot / Kimi
    "alibaba-ai",   # Qwen / 通义
]

SOURCES = [
    (f"VPSDance/{name}", f"{BASE}/{name}.list") for name in SERVICES
]

# Grok (xAI) has no VPSDance list; add manually.
EXTRA_SUFFIXES = {"grok.com", "x.ai"}

# Overlap with muse-rules repo; excluded here so the two sets are disjoint.
EXCLUDE_DOMAINS = {
    "atmeta.com",
    "llama.com",
    "llamameta.net",
    "meta.ai",
    "metaaivm.com",
    "muse.ai",
}

OUTPUT_LIST = "AI-merged.list"
OUTPUT_ARRS = "AI.arrs"
ARRS_NAME = "AI"


def fetch(name, url):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-rules-merge/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8", errors="replace")
    print(f"fetched {name}: {len(text)} chars", flush=True)
    return text


def parse(text):
    """Return (suffixes, domains, keywords, cidr4, cidr6, skipped)."""
    suffixes, domains, keywords, cidr4, cidr6 = set(), set(), set(), set(), set()
    skipped = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        kind, value = parts[0].upper(), parts[1].lower()
        if kind == "DOMAIN-SUFFIX" and value:
            suffixes.add(value)
        elif kind == "DOMAIN" and value:
            domains.add(value)
        elif kind == "DOMAIN-KEYWORD" and value:
            keywords.add(value)
        elif kind == "IP-CIDR" and value:
            cidr4.add(parts[1])  # keep original case for CIDR
        elif kind == "IP-CIDR6" and value:
            cidr6.add(parts[1])
        elif kind:
            skipped[kind] = skipped.get(kind, 0) + 1
    return suffixes, domains, keywords, cidr4, cidr6, skipped


def covered_by_suffix(name, suffixes):
    return any(name == s or name.endswith("." + s) for s in suffixes)


def dedupe(suffixes, domains):
    """Drop suffixes shadowed by a broader suffix and domains covered by one."""
    suffixes = sorted(s for s in suffixes if not any(
        s != o and (s == o or s.endswith("." + o)) for o in suffixes))
    suffix_set = set(suffixes)
    domains = sorted(d for d in domains if not covered_by_suffix(d, suffix_set))
    return suffixes, domains


def write_list(suffixes, domains, keywords, cidr4, cidr6, today):
    lines = [
        "# 精选 AI 服务分流规则集 (自动生成, 每日更新)",
        "#",
        "# 来源: VPSDance/ai-proxy-rules 按服务精选",
        "#   (openai, anthropic, google-ai, deepseek, cursor, copilot,",
        "#    perplexity, midjourney, groq, poe, openrouter, mistral-ai,",
        "#    moonshot-ai, alibaba-ai) + 手动补充 Grok",
        "# 注: 与 muse-rules 重叠的 6 个 Meta AI 域名已剔除",
        f"# 生成日期: {today}",
        "",
        "# === DOMAIN-SUFFIX ===",
        *[f"DOMAIN-SUFFIX,{s}" for s in suffixes],
        "",
        "# === DOMAIN (精确域名, 未被上方后缀覆盖) ===",
        *[f"DOMAIN,{d}" for d in domains],
        "",
        "# === DOMAIN-KEYWORD ===",
        *[f"DOMAIN-KEYWORD,{k}" for k in sorted(keywords)],
        "",
        "# === IP-CIDR ===",
        *[f"IP-CIDR,{c}" for c in sorted(cidr4)],
        "",
        "# === IP-CIDR6 ===",
        *[f"IP-CIDR6,{c}" for c in sorted(cidr6)],
        "",
    ]
    with open(OUTPUT_LIST, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"wrote {OUTPUT_LIST}", flush=True)


def write_arrs(suffixes, domains, keywords, cidr4, cidr6, skipped, today):
    rules = (
        [f"2, {s}" for s in suffixes]
        + [f"2, {d}" for d in domains]
        + [f"3, {k}" for k in sorted(keywords)]
        + [f"0, {c}" for c in sorted(cidr4)]
        + [f"1, {c}" for c in sorted(cidr6)]
    )
    source_urls = [url for _, url in SOURCES]
    skipped_total = sum(skipped.values())
    lines = [
        f"# NAME: {ARRS_NAME}",
        "# GENERATED-FOR: Anywhere Routing Rule Set",
        "# DESCRIPTION: 精选 AI 服务分流规则（Anywhere 专用，自动生成，每日更新）",
        f"# RULES: {len(rules)}",
        f"# SKIPPED: {skipped_total}",
    ]
    if skipped:
        lines.append("# SKIPPED-TYPES: " + ", ".join(
            f"{k}={v}" for k, v in sorted(skipped.items())))
    lines += [
        "# SOURCES:",
        *[f"# - {u}" for u in source_urls],
        "# - manual: Grok (grok.com, x.ai)",
        "#",
        "# 注: 与 muse-rules 重叠的 6 个 Meta AI 域名已剔除，",
        "# 两个规则集可指向不同节点。",
        "# 导入后请手动把该规则集指向你的代理策略组。",
        f"# 生成日期: {today}",
        "",
        f"name = {ARRS_NAME}",
        *rules,
        "",
    ]
    with open(OUTPUT_ARRS, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"wrote {OUTPUT_ARRS}: {len(rules)} rules, skipped {skipped_total}", flush=True)


def main():
    suffixes, domains, keywords, cidr4, cidr6 = set(), set(), set(), set(), set()
    skipped_total = {}
    for name, url in SOURCES:
        try:
            text = fetch(name, url)
        except Exception as e:  # noqa: BLE001 - one bad source must not kill the merge
            print(f"WARN: failed to fetch {name}: {e}", file=sys.stderr, flush=True)
            continue
        s, d, k, c4, c6, sk = parse(text)
        suffixes |= s
        domains |= d
        keywords |= k
        cidr4 |= c4
        cidr6 |= c6
        for t, n in sk.items():
            skipped_total[t] = skipped_total.get(t, 0) + n

    # Manual additions
    suffixes |= EXTRA_SUFFIXES

    if not (suffixes or domains or keywords or cidr4 or cidr6):
        print("ERROR: no rules fetched, refusing to write empty output",
              file=sys.stderr, flush=True)
        sys.exit(1)

    suffixes, domains = dedupe(suffixes, domains)

    # Exclude overlap with muse-rules so the two sets are disjoint
    suffixes = [s for s in suffixes if s not in EXCLUDE_DOMAINS]
    domains = [d for d in domains if d not in EXCLUDE_DOMAINS]

    today = datetime.date.today().isoformat()
    write_list(suffixes, domains, keywords, cidr4, cidr6, today)
    write_arrs(suffixes, domains, keywords, cidr4, cidr6, skipped_total, today)


if __name__ == "__main__":
    main()
