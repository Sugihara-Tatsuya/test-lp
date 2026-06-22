# xOrder API アクセスログ ボトム20エンドポイント レポート

**期間:** 直近30日 (2026-05-22 ~ 2026-06-21)
**データソース:** xorder-log-to-bigquery パイプライン経由のnginxアクセスログ

---

## 1. BQテーブル構成 (リポから特定)

| GCPプロジェクト | データセット | テーブル名 | 対応サービス | 30日間レコード数 |
|---|---|---|---|---|
| xorder-354202 | logs | api_nginx_logs | xorder-api (xmart-web-api) | 308,743,151 |
| xorder-354202 | logs | shop_nginx_logs | xorder-shop (xmart-web-shop-ordering) | 1,847,840 |
| xorder-354202 | logs | admin_legacy_nginx_logs | xorder-admin-legacy (xmart-web-admin-ordering) | 69,545 |
| xorder-354202 | logs | supplier_nginx_logs | xorder-supplier (xmart-web-supplier-ordering) | 15,407,036 |
| xorder-354202 | dashboard | api_nginx_logs | xorder-dashboard-api | 43,506 |
| xorder-kyushoku-production | logs | api_nginx_logs | xorder-kyushoku-api | 7,306,568 |
| xorder-auth | logs | api_nginx_logs | xorder-auth-api | 92,838 |
| xorder-auth | logs | api_internal_nginx_logs | xorder-auth-api (internal) | 38,776 |

**スキーマ (全テーブル共通):** `timestamp`, `remote_addr`, `request_time`, `request_method`, `path`, `request_body`, `response_status`, `cookie`, `set_cookie`, `size`, `host`, `xo_user_id`*, `x_forwarded_for`, `user_agent`, `upstream_addr`, `upstream_response_time`, `referrer`, `protocol`, `lambda_timestamp`
(*`xo_user_id`はorder系テーブルのみ)

全テーブルは `lambda_timestamp` で日次パーティショニング済み。

---

## 2. GA4エクスポートテーブルの有無

| プロジェクト | データセット | GA4テーブル有無 | 備考 |
|---|---|---|---|
| xorder-354202 | xmart_analytics | **あり (過去データのみ)** | `events_YYYYMMDD` 形式のテーブルが存在 (2023-06-27 ~ 2023-09-22)。最終データは2023年9月で**現在は更新停止**。他に `ga_event_log_20230101_20230726`, `maker_ad_repeat_purchase` も存在。 |
| xorder-354202 | 他のデータセット | なし | `analytics_*` パターンのデータセットは存在しない |
| xorder-kyushoku-production | - | なし | `logs`, `snapshot` のみ |
| xorder-auth | - | なし | `logs` のみ |

**結論:** GA4エクスポートテーブルは `xorder-354202.xmart_analytics` に過去データ (2023年6~9月) として存在するが、現在はアクティブに更新されていない。標準的な `analytics_XXXXXXXX` データセット命名のGA4エクスポートは存在しない。

---

## 3. ボトム20エンドポイント (直近30日, call_count >= 5)

**除外条件:** ヘルスチェック系, メトリクス系, OPTIONS/HEAD, 静的アセット, Swagger/OpenAPI, 攻撃/スキャントラフィック (.php, .env, wp-*, etc.)

**パス正規化:** 数値ID → `:id`, UUID → `:uuid`, 日付 → `:date`, LINE ID → `:line_id`, hexハッシュ → `:hash`, base64トークン → `:token`, 商品コード → `:code`

**`unique_tenants_30d` について:** `host` カラムをテナント代替指標として使用。本システムは `api.xmart.co.jp` と `api-internal.xorder.jp` の2ホストで運用されているため、値は1~2に集中する（マルチテナントのサブドメイン分離ではない）。

| endpoint | http_method | call_count_30d | unique_tenants_30d | last_called_at | repository_hint | notes |
|---|---|---|---|---|---|---|
| /catalog/list/edit/ | GET | 5 | 1 | 2026-06-11 13:41:48 UTC | xmart-web-supplier-ordering | サプライヤーWebカタログ編集画面 |
| /suppliers/:id/order-settings/labels/:id/update/ | POST | 5 | 1 | 2026-06-17 03:06:22 UTC | xmart-web-admin-ordering | 注文設定ラベル更新 |
| /supplier_users/base | GET | 5 | 1 | 2026-06-16 06:25:50 UTC | xmart-web-supplier-ordering | サプライヤーユーザー基本情報 |
| /supplier_order/me/shops/:id/products_v2/undefined | GET | 5 | 1 | 2026-06-20 00:57:40 UTC | xmart-web-api | **`undefined`が含まれる - フロントエンドバグの可能性** |
| /ordering/suppliers/:id/shop_collection | GET | 5 | 1 | 2026-06-19 01:45:24 UTC | xmart-web-admin-ordering | サプライヤー店舗コレクション |
| /ordering/suppliers/:id/multi-unit-product-migration | GET | 5 | 1 | 2026-06-05 01:14:39 UTC | xmart-web-admin-ordering | 複数単位商品マイグレーション |
| /shop_order_supplier/:id/subscription_delivery/info/:id/read | PUT | 5 | 1 | 2026-06-18 04:21:10 UTC | xmart-web-api | 定期配送情報既読マーク |
| /ordering/suppliers/:id/shops/csv | POST | 5 | 1 | 2026-06-10 13:20:25 UTC | xmart-web-admin-ordering | 店舗一覧CSVエクスポート |
| /invoice/suppliers/:id/shops/3907-01/lines | GET | 5 | 1 | 2026-06-20 02:46:14 UTC | xmart-web-api | 店舗コード `3907-01` が正規化未対応 |
| /ordering/suppliers/:id/:token/:id/catalog-product-master-csv | POST | 5 | 1 | 2026-06-15 03:11:30 UTC | xmart-web-admin-ordering | カタログ商品マスタCSVエクスポート |
| /supplier_order/me/subscription_delivery/:id/schedule/:id/update_quantity | PUT | 5 | 1 | 2026-06-18 04:59:47 UTC | xmart-web-api | 定期配送スケジュール数量更新 |
| /order/inbox | GET | 5 | 1 | 2026-06-15 02:01:09 UTC | xmart-web-supplier-ordering | サプライヤー注文受信ボックス |
| /supplier_order/me/catalog-record/bulk_file_upload_template_csv | GET | 5 | 1 | 2026-06-19 04:58:21 UTC | xmart-web-api | カタログ一括アップロードテンプレートCSV |
| /subscription-delivery/create | GET | 5 | 1 | 2026-06-18 01:49:18 UTC | xmart-web-supplier-ordering | 定期配送作成画面 |
| /supplier_order/me/shop-code-map | GET | 5 | 1 | 2026-06-17 10:31:12 UTC | xmart-web-api | 店舗コードマッピング取得 |
| /order/edit/complete | GET | 5 | 1 | 2026-06-08 16:37:00 UTC | xmart-web-shop-ordering | 注文編集完了画面 |
| /ordering/suppliers/:id/order-delivery-csv | GET | 5 | 1 | 2026-06-10 09:10:15 UTC | xmart-web-admin-ordering | 注文配送CSVダウンロード |
| /error/trade-suspended | GET | 5 | 1 | 2026-06-17 18:10:21 UTC | xmart-web-shop-ordering | 取引停止エラーページ |
| /ordering/suppliers/:id/order_supplier/csv | POST | 5 | 1 | 2026-06-11 09:42:30 UTC | xmart-web-admin-ordering | 発注先CSV操作 |
| /operator/suppliers/:id/shop-group-csv | GET | 5 | 1 | 2026-06-19 01:47:10 UTC | xmart-web-api | 店舗グループCSVダウンロード |

---

## 4. 所見

1. **ボトム20の大半は管理系CSV操作・設定系エンドポイント**: 管理者(admin-legacy)が手動で行うCSVエクスポート/インポートが多く、日常的な利用頻度が非常に低い。
2. **`undefined` バグ**: `/supplier_order/me/shops/:id/products_v2/undefined` はフロントエンドで変数が未定義のままAPIに送信されている可能性がある。要調査。
3. **定期配送系が低頻度**: `subscription_delivery` 関連エンドポイントの利用が極めて少なく、機能の利用状況を要確認。
4. **店舗コードの正規化**: `/invoice/suppliers/:id/shops/3907-01/lines` のような店舗コードパラメータは正規化しきれていないため、実際の集計値はさらに小さい可能性がある。

---

## 5. クエリ詳細

- **スキャン量**: 約31GB (全テーブル30日分の `path`, `request_method`, `host`, `lambda_timestamp` カラム)
- **正規化ルール**: UUID, 日付, 数値ID, hexハッシュ, base64トークン, LINE ID, 商品コード, 認証トークン等を正規化
- **最低閾値**: `call_count >= 5` (ノイズ除去のため。1~4件のエンドポイントは大半がセキュリティスキャンや一回限りのリクエスト)
