# xOrder 機能利用分析（Feature Pruning）

## プロジェクト概要
xOrder の低利用機能を特定し、廃止候補をランク付けする調査プロジェクト。

## 調査ステータス: Phase 4 完了（最終ランク付け済み）

## 成果物

### ローカルファイル
| ファイル | 内容 |
|---|---|
| `01-bottom20-endpoints.md` | Phase 1: グローバルボトム20エンドポイント |
| `01-bottom20-by-service.md` | Phase 1: サービス別ボトム20（9セクション） |
| `02-feature-estimation.md` | Phase 2: 36エンドポイントの機能意味推定 |
| `03-ga4-cross-reference.md` | Phase 3: GA4 PVデータとのクロスリファレンス |
| `SESSION_LOG.md` | Devin セッション管理ログ |

### Notion
- 詳細レポート: https://app.notion.com/p/386e9a364d1b813c9eecf84e7a27fd7b
- 非エンジニア向けサマリー（子ページ）: https://app.notion.com/p/387e9a364d1b8128bf2be7e266b2a037

### Devin セッション
| Phase | Session URL | Status |
|---|---|---|
| Phase 1 | https://app.devin.ai/sessions/cfa28afd6503416da7cc88f979c7d0ff | archived |
| Phase 2 | https://app.devin.ai/sessions/3c430384f86b4bd39eb59db22f2cedce | archived |
| Phase 3 | https://app.devin.ai/sessions/3b6ef3f4beb441f3bce43caf30cd642e | completed |

## 最終結論

### 即廃止推奨（5件）
- /member/agree, /list/discontinued（コード未発見）
- /order/history-deadline/shops/（PV=2）
- /supplier/:id/order_plan/this-month/delete, /supplier/:id/ftp（新admin-orderingに移行済み）

### Legacy admin 一括廃止推奨（12件）
- 旧管理画面（xmart-web-admin）の設定系・削除系・CSV系。全件月1回利用

### 回収機能 精査推奨（4件）
- collection 関連。利用企業の確認が必要

### 追加調査必要（8件）
- 定期配送2件（利用者ヒアリング）、給食系6件（チーム確認）

### バグ修正（即対応）
- /supplier_order/me/shops/:id/products_v2/undefined → フロントエンドバグ

## データソース
- BQ: xorder-354202, xorder-kyushoku-production, xorder-auth（8テーブル、30日間3.3億行）
- GA4: 5プロパティ（xorder, xorder-supplier, kyushoku-shop, kyushoku-supplier, dashboard-supplier）
- GA4認証: サービスアカウント ga4-mcp-reader@xmart-ga4-mcp.iam.gserviceaccount.com（キーは .mcp.json）

## 注意事項
- .mcp.json にサービスアカウントの秘密鍵が含まれる。コミット禁止
- GA4 MCPはローカルのnpx起動だが、このセッションではツール登録されなかった。Devin経由でPython+GA4 Data APIで代替した
