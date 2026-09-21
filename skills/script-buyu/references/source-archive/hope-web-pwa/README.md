# Hope Web PWA

Hope Web PWA 是 Hope 分镜工作台的浏览器版本，当前目标是走通这条产品链：

原始文本 -> KB 写作组参与扩写/改写 -> 用户确认 accepted body -> 创建 storyboard task -> 生成 storyboard rows -> 用户确认当前镜头 -> 导出用户可交付结果

当前目录 `E:\codex\hope-web-pwa` 不是 Git 仓库，交付和核对都以实际文件状态为准。

## 安装

```bash
npm install
```

## 本地运行

开发模式：

```bash
npm run dev
```

构建并预览：

```bash
npm run build
npm run preview
```

默认地址：

- 开发：`http://127.0.0.1:4173/`
- 预览：`http://127.0.0.1:4174/`

## 使用链路

1. 打开页面，配置 `provider / base_url / endpoint / model / API Key`。
2. 点击“测试连接”，确认浏览器直连可用。
3. 输入或导入原始文本，选择 `scene_type` 和时长。
4. 点击“扩写故事”或“改写故事”。
5. 检查正文草稿，确认后点击“确定使用”。
6. 新建镜头任务。
7. 点击“开始生成”，得到当前分镜结果。
8. 如有人工修改，必须再次点击“确认当前镜头”恢复 `fresh`。
9. 导出分镜词或完整剧本。

## KB 契约边界

唯一契约来源：

- `E:\codex\hope-kb\docs\kb-product-chain-contract-v0.2.md`

WebPWA 只消费 summary-only KB 结果，不接 raw KB rows，不接 raw sample_text，不接 `source_register`，不接 `overlay_json`，不接 `prompt_body`。

当前实现会在运行时检查这些最小边界：

- `raw_kb_rows_included = 0`
- `raw_sample_text_absent = true`
- `source_register_absent = true`
- `overlay_json_absent = true`
- `prompt_body_absent = true`

## 安全规则

- API Key 默认只在当前会话保留。
- 只有用户显式允许时，API 配置才会写入浏览器持久存储。
- UI 不应显示 sample ids、rule ids、hash refs 或内部 evidence。
- 用户导出不得包含：
  - raw KB rows
  - raw sample text
  - `source_register`
  - `overlay_json`
  - `prompt_body`
  - sample ids
  - rule ids
  - internal hash / ref
  - API key / token / local path

## QA 命令

```bash
npm test
npm run build
node tests/qa/web-formal403-runner.mjs --plan-only
npm run targeted
npm run full16
npm run formal403:live
```

说明：

- `plan-only` 只核对 `4 + 378 + 21 = 403` 的结构，不算 formal403 完成。
- `targeted` 是小范围 fresh 验证。
- `full16` 要求 16/16 全通过。
- `formal403:live` 要求 403/403 全通过。

## Fresh 规则

- runner 每次都必须创建新的 artifact root。
- 不允许把旧 `.codex-run` partial 当通过证据。
- `rows=0`、`rows_match=true`、旧 artifact、plan-only、partial run 都不能算成功。

## Live Run 前提

live runner 依赖两个前提：

1. 预览站点在线：

```bash
npm run preview
```

2. 当前 shell 提供可用 API key：

- `HOPE_WEB_API_KEY`
- 或 `HOPE_TEXT_MODEL_API_KEY`

如果预览站点未启动，或 key 未注入，`targeted / full16 / formal403` 会在进入浏览器前直接失败。

## 交付 `dist/`

先构建：

```bash
npm run build
```

推荐预览或交付方式：

```bash
npx serve dist
```

说明：

- 当前构建按根路径部署。
- 不建议直接双击 `dist/index.html` 用 `file://` 打开。
- 交付时至少应同时提供：
  - `dist/`
  - 本 README
  - 使用方需要自行提供的 API key / provider 配置说明
