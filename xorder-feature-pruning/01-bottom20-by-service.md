# サービス別 ボトム20エンドポイント レポート

**期間:** 直近30日 (2026-05-22 ~ 2026-06-21)
**条件:** 同一の除外条件・正規化ルール適用、call_count >= 1

---

## 1. xorder-api ボトム20

（テーブル30日間総リクエスト数（除外後）: **249,366,163**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /invoice/suppliers/:id/shops/o038/lines | GET | 1 | 2026-05-30 07:47:53 UTC | 店舗コード未正規化 |
| /supplier_order/password_token_check/MjI2MTc5/d9clnt-…/ | GET | 1 | 2026-05-29 07:27:14 UTC | パスワードリセットトークン未正規化 |
| /supplier_order/password_token_check/MzA5OTcy/da4paz-…/ | GET | 1 | 2026-06-13 11:38:02 UTC | 同上 |
| /supplier_order/password_token_check/MTU3MDA4/d98bzz-…/ | GET | 1 | 2026-05-27 00:19:02 UTC | 同上 |
| /supplier_order/password_token_check/MzA5OTI4/d9eqza-…/ | GET | 1 | 2026-05-30 11:16:52 UTC | 同上 |
| /invoice/suppliers/:id/shops/4166-0/lines | GET | 1 | 2026-05-26 02:59:29 UTC | 店舗コード未正規化 |
| /invoice/suppliers/:id/shops/7034-0/lines | GET | 1 | 2026-05-26 02:59:44 UTC | 店舗コード未正規化 |
| /supplier_order/me/supplier-user-csv/upload/template_csv | GET | 1 | 2026-05-28 02:46:21 UTC | サプライヤーユーザーCSVテンプレート |
| /invoice/suppliers/:id/shops/G1902/lines | GET | 1 | 2026-06-01 09:09:54 UTC | 店舗コード未正規化 |
| /supplier_shop_order_group/me/shop-csv/upload/:id/download_error_only | GET | 1 | 2026-06-20 08:07:35 UTC | CSVアップロードエラーDL |
| /invoice/suppliers/:id/shops/4699-01/lines | GET | 1 | 2026-06-02 07:56:14 UTC | 店舗コード未正規化 |
| /supplier_order/password_token_check/NDAyNTI3/da97pf-…/ | GET | 1 | 2026-06-15 22:06:02 UTC | パスワードリセットトークン未正規化 |
| /supplier_order/password_token_check/NDUyMzg2/da7im7-…/ | GET | 1 | 2026-06-15 00:06:51 UTC | 同上 |
| /collection/route | POST | 1 | 2026-06-13 02:57:54 UTC | コレクション配送ルート |
| /collection/shop-supplier/group | POST | 1 | 2026-06-13 02:54:34 UTC | コレクション店舗グループ |
| /invoice/suppliers/:id/shops/G3192/lines | GET | 1 | 2026-06-01 10:32:23 UTC | 店舗コード未正規化 |
| /supplier_order/password_token_check/NDc4MTk5/d9m436-…/ | GET | 1 | 2026-06-03 10:42:56 UTC | パスワードリセットトークン未正規化 |
| /supplier_order/me/v2/catalogs/:id | DELETE | 1 | 2026-06-01 04:43:30 UTC | カタログ削除 |
| /invoice/suppliers/:id/shops/G3204/lines | GET | 1 | 2026-06-01 10:22:08 UTC | 店舗コード未正規化 |
| /invoice/suppliers/:id/shops/3979-01/lines | GET | 1 | 2026-06-02 07:30:57 UTC | 店舗コード未正規化 |

> **所見:** ボトム20の大半は `/invoice/.../shops/{shop_code}/lines`（店舗コードが正規化できず個別パスとしてカウント）と `/supplier_order/password_token_check/`（base64+ハッシュのトークンが正規化未対応）。実質的な低頻度APIは `collection/route`, `collection/shop-supplier/group`, `supplier_order/me/v2/catalogs/:id DELETE`, `supplier_order/me/supplier-user-csv/upload/template_csv`。

---

## 2. xorder-shop ボトム20

（テーブル30日間総リクエスト数（除外後）: **1,731,372**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /old1 | GET | 1 | 2026-06-16 03:40:31 UTC | スキャナトラフィック |
| /beta | GET | 1 | 2026-06-16 03:45:52 UTC | スキャナトラフィック |
| /settings.py | GET | 1 | 2026-05-31 21:33:20 UTC | スキャナトラフィック |
| /graphql/console | GET | 1 | 2026-05-31 21:33:45 UTC | スキャナトラフィック |
| /company/corporate-profile/ | GET | 1 | 2026-06-10 01:28:40 UTC | 会社概要サブページ |
| /api/graphql | GET | 1 | 2026-05-31 21:33:45 UTC | スキャナトラフィック |
| /dev | GET | 1 | 2026-06-16 03:44:27 UTC | スキャナトラフィック |
| /api/v2/settings | GET | 1 | 2026-05-31 21:33:40 UTC | スキャナトラフィック |
| /company/corporate-data/ | GET | 1 | 2026-06-10 01:28:35 UTC | 会社概要サブページ |
| /up | GET | 1 | 2026-06-16 03:41:26 UTC | スキャナトラフィック |
| /uat | GET | 1 | 2026-06-16 03:45:41 UTC | スキャナトラフィック |
| /cms | GET | 1 | 2026-06-16 03:39:31 UTC | スキャナトラフィック |
| /api/health | GET | 1 | 2026-05-31 21:33:40 UTC | スキャナトラフィック |
| /9dd2d89aad02598a12aebe.mpg | GET | 1 | 2026-06-04 10:07:38 UTC | スキャナトラフィック |
| /api/Event/basic | GET | 1 | 2026-05-31 08:00:20 UTC | スキャナトラフィック |
| /blog | GET | 1 | 2026-06-16 03:41:31 UTC | スキャナトラフィック |
| /staging | GET | 1 | 2026-06-16 03:38:31 UTC | スキャナトラフィック |
| /copy | GET | 1 | 2026-06-16 03:44:37 UTC | スキャナトラフィック |
| /blogs | GET | 1 | 2026-06-16 03:44:57 UTC | スキャナトラフィック |
| /oldwebsite | GET | 1 | 2026-06-16 03:40:51 UTC | スキャナトラフィック |

> **所見:** ボトム20のほぼ全件がセキュリティスキャナ/ボットによるプロービング。正規エンドポイントは `/company/corporate-profile/` と `/company/corporate-data/` のみ（各1回）。

---

## 3. xorder-admin-legacy ボトム20

（テーブル30日間総リクエスト数（除外後）: **35,683**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /suppliers/:id/order-settings/split/:id/delete/ | GET | 1 | 2026-06-06 14:44:39 UTC | 注文設定分割削除 |
| /ordering/suppliers/:id/shop_collection/setting/:id | GET | 1 | 2026-05-26 06:09:09 UTC | コレクション設定参照 |
| /ordering/suppliers/:id/shop_collection/setting/:id | POST | 1 | 2026-05-26 06:09:14 UTC | コレクション設定更新 |
| /order_supplier/:id/share_email/:id/update | GET | 1 | 2026-06-19 14:20:39 UTC | 共有メール更新画面 |
| /supplier/:id/order_plan/this-month/delete | POST | 1 | 2026-06-01 05:36:59 UTC | 当月注文計画削除 |
| /api/operator/zips/910-0823 | GET | 1 | 2026-06-17 09:10:13 UTC | 郵便番号検索（未正規化） |
| /:token/:id/products-csv/:id/download/error_upload_csv | GET | 1 | 2026-06-18 06:57:51 UTC | 商品CSVエラーDL |
| /order_option_plan/update/:id | GET | 1 | 2026-06-10 05:11:41 UTC | 注文オプション計画更新 |
| /api/operator/zips/362-0077 | GET | 1 | 2026-06-02 02:00:29 UTC | 郵便番号検索（未正規化） |
| /supplier/:id/order_plan/this-month/delete | GET | 1 | 2026-06-01 05:36:54 UTC | 当月注文計画削除画面 |
| /ordering/suppliers/:id/price-csv/unit-splitter-setting | GET | 1 | 2026-05-29 08:13:54 UTC | 価格CSV単位分割設定 |
| /suppliers/:id/order-settings/tag/:id/delete/ | POST | 1 | 2026-06-03 11:49:04 UTC | 注文設定タグ削除 |
| /api/operator/order/:id/pdf/download | GET | 1 | 2026-06-19 01:14:36 UTC | 注文PDFダウンロード |
| /ordering/suppliers/:id/shops/relation/:id/password | GET | 1 | 2026-06-04 02:49:34 UTC | 店舗関連パスワード |
| /ordering/suppliers/:id/records/:id/delete | GET | 1 | 2026-06-04 04:48:44 UTC | レコード削除 |
| /claim/:id | GET | 1 | 2026-06-02 06:59:49 UTC | クレーム詳細 |
| /ordering/suppliers/:id/shop_collection/create | GET | 1 | 2026-05-26 06:09:09 UTC | コレクション作成 |
| /supplier/:id/ftp | GET | 1 | 2026-05-28 03:29:24 UTC | FTP設定画面 |
| /ordering/suppliers/:id/catalog-product-master-csv/unit-splitter-setting | GET | 1 | 2026-05-29 08:13:44 UTC | カタログCSV単位分割設定 |
| /ordering/suppliers/:id/flyer/product | GET | 1 | 2026-06-08 07:58:31 UTC | チラシ商品管理 |

> **所見:** 全件 call_count=1。admin-legacy は総リクエスト数自体が少なく（35,683件/30日）、管理者が低頻度で使う設定系・削除系・CSV関連操作が多い。

---

## 4. xorder-supplier ボトム20

（テーブル30日間総リクエスト数（除外後）: **1,257,364**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /downloader/catalog/BDAV_ALL/:id | GET | 1 | 2026-05-26 12:52:39 UTC | カタログDL（商品コード未正規化） |
| /order/history-deadline/shops/ | GET | 1 | 2026-06-07 08:43:49 UTC | 注文履歴期限 |
| /downloader/catalog/ORCA_ALL/:id | GET | 1 | 2026-05-30 03:25:56 UTC | カタログDL |
| /downloader/catalog/F_SERIES_ALL/:id | GET | 1 | 2026-06-12 00:19:08 UTC | カタログDL |
| /order | GET | 1 | 2026-05-26 06:28:17 UTC | 注文トップ |
| /service/~iufo/com.ufida.web.action.ActionServlet | GET | 1 | 2026-05-28 14:41:41 UTC | スキャナトラフィック |
| /member/agree | GET | 1 | 2026-05-31 01:41:16 UTC | 会員規約同意画面 |
| /dealshops/delivery_group/specified/edit | GET | 1 | 2026-06-16 05:40:17 UTC | 配送グループ編集 |
| /downloader/catalog/180_ALL/:id | GET | 1 | 2026-05-23 13:44:07 UTC | カタログDL |
| /downloader/catalog/8Z_SW_MODULE/:id | GET | 1 | 2026-05-28 14:15:46 UTC | カタログDL |
| /downloader/catalog/FMA_ALL/:id | GET | 1 | 2026-05-25 03:23:23 UTC | カタログDL |
| /downloader/catalog/F15M_FP/:id | GET | 1 | 2026-06-14 18:21:18 UTC | カタログDL |
| /collection/bottle/ | GET | 1 | 2026-05-30 06:33:16 UTC | ボトルコレクション |
| /list/discontinued | GET | 1 | 2026-05-25 02:17:05 UTC | 廃番商品一覧 |
| /downloader/catalog/ZC630_653/:id | GET | 1 | 2026-05-25 17:32:28 UTC | カタログDL |
| /downloader/catalog/8_BRACKET_ALL/:id | GET | 1 | 2026-05-28 02:35:49 UTC | カタログDL |
| /collection/shop/ | GET | 1 | 2026-06-14 13:06:13 UTC | 店舗コレクション |
| /uapjs/jsinvoke/ | POST | 1 | 2026-05-28 14:42:56 UTC | スキャナトラフィック |
| /magento_version | GET | 1 | 2026-06-02 08:21:27 UTC | スキャナトラフィック |
| /:token | POST | 1 | 2026-06-03 12:41:30 UTC | 不明（トークン正規化済み） |

> **所見:** `/downloader/catalog/{code}/:id` が多数ランクイン（商品コードが正規化されず個別カウント）。正規化するとより集約される。正規エンドポイントとして `/order/history-deadline/shops/`, `/member/agree`, `/dealshops/delivery_group/specified/edit`, `/list/discontinued` が低頻度。

---

## 5. xorder-dashboard ボトム20

（テーブル30日間総リクエスト数（除外後）: **20,936**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /_cluster/state | GET | 1 | 2026-06-17 20:01:14 UTC | スキャナトラフィック |
| /private/sendgrid_config | GET | 1 | 2026-06-17 19:56:19 UTC | スキャナトラフィック |
| /backend | GET | 1 | 2026-06-17 20:04:54 UTC | スキャナトラフィック |
| /_debugbar/open | GET | 1 | 2026-06-17 19:49:59 UTC | スキャナトラフィック |
| /__debug__/doc/bookmarklets/* | GET | 1 | 2026-06-17 19:53:49 UTC | スキャナトラフィック |
| /rails/info/routes | GET | 1 | 2026-06-17 20:04:29 UTC | スキャナトラフィック |
| /rest/workflows/run | GET | 1 | 2026-06-17 19:55:09 UTC | スキャナトラフィック |
| /rest/license | GET | 1 | 2026-06-17 19:56:14 UTC | スキャナトラフィック |
| /core/assets/ | GET | 1 | 2026-06-17 20:02:54 UTC | スキャナトラフィック |
| /__debug__ | GET | 1 | 2026-06-17 19:56:39 UTC | スキャナトラフィック |
| /api/v2/docs | GET | 1 | 2026-06-17 20:06:44 UTC | スキャナトラフィック |
| /signup | GET | 1 | 2026-06-17 20:05:34 UTC | スキャナトラフィック |
| /sites/default/files/backup_migrate/scheduled/ | GET | 1 | 2026-06-17 20:03:19 UTC | スキャナトラフィック |
| /shop/[category]/* | GET | 1 | 2026-06-17 19:59:24 UTC | スキャナトラフィック |
| /admin-api/ | GET | 1 | 2026-06-17 19:56:04 UTC | スキャナトラフィック |
| /graphiql/ | GET | 1 | 2026-06-17 20:06:14 UTC | スキャナトラフィック |
| /api/private/ | GET | 1 | 2026-06-17 20:04:44 UTC | スキャナトラフィック |
| /__debug__/history/ | GET | 1 | 2026-06-17 19:54:19 UTC | スキャナトラフィック |
| /static/admin/fonts/ | GET | 1 | 2026-06-17 19:49:49 UTC | スキャナトラフィック |
| /api/admin | GET | 1 | 2026-06-17 19:50:24 UTC | スキャナトラフィック |

> **所見:** 全20件が 2026-06-17 の同一時間帯（19:49〜20:06）に集中。**完全にセキュリティスキャナによるプロービング**。正規の低頻度エンドポイントはボトム20に入っていない。

---

## 6. xorder-kyushoku ボトム20

（テーブル30日間総リクエスト数（除外後）: **4,990,047**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /kyushoku/me/kyushoku-group/csv/:id/fix | GET | 1 | 2026-06-04 02:30:23 UTC | グループCSV修正 |
| /:token/:id/use-date/:date/inspection-department-csv/ | GET | 1 | 2026-06-15 04:12:15 UTC | 検収部門CSV |
| /admin/supplier-product-matching/:id | DELETE | 1 | 2026-05-27 04:47:53 UTC | サプライヤー商品マッチング削除 |
| /kyushoku/me/kyushoku-group/:id/csv/order/products/delivery-date | PUT | 1 | 2026-06-05 08:13:17 UTC | グループCSV配送日更新 |
| /admin/kyushoku/:id/csv/:id/error | GET | 1 | 2026-06-18 02:32:59 UTC | CSVエラー確認 |
| /:token/:id/10/shop/:id/use-date | GET | 2 | 2026-06-06 11:03:18 UTC | 月別利用日（10月） |
| /:token/:id/11/shop/:id/use-date | GET | 2 | 2026-06-06 11:03:27 UTC | 月別利用日（11月） |
| /:token/:id/9/shop/:id/use-date | GET | 2 | 2026-06-13 00:14:32 UTC | 月別利用日（9月） |
| /:token/:id/ | GET | 2 | 2026-06-03 06:47:53 UTC | 不明（トークン正規化済み） |
| /:token/:id/has-unread/ | GET | 2 | 2026-06-03 06:47:53 UTC | 未読チェック |
| /kyushoku/me/shops/:id/messages/latest/ | GET | 2 | 2026-06-03 06:47:53 UTC | 最新メッセージ |
| /kyushoku/me/shops/:id/messages/unread/ | GET | 2 | 2026-06-03 06:47:53 UTC | 未読メッセージ |
| /kyushoku/me/orders/product-order/ | GET | 2 | 2026-06-08 09:29:28 UTC | 商品発注一覧 |
| /:token/:id/12/shop/:id/use-date | GET | 4 | 2026-06-09 08:44:18 UTC | 月別利用日（12月） |
| /kyushoku/me/kyushoku-group/csv/columns | POST | 4 | 2026-05-29 04:20:25 UTC | グループCSVカラム設定 |
| /:token/:id/has_unread | GET | 6 | 2026-06-12 05:21:57 UTC | 未読チェック |
| /:token/:id/update | GET | 6 | 2026-06-12 08:19:19 UTC | 更新画面 |
| /kyushoku/me/orders/:id/inspection-department-csv | GET | 7 | 2026-06-19 03:21:41 UTC | 検収部門CSV |
| /kyushoku/me/kyushoku-group/csv/:id/error | GET | 7 | 2026-06-16 04:20:28 UTC | CSVエラー確認 |
| /suppliers/me/proxy-order/csv/columns | POST | 8 | 2026-06-17 07:35:21 UTC | 代理発注CSVカラム設定 |

> **所見:** スキャナトラフィックが少なく、ほぼ全件が正規エンドポイント。給食系のCSV操作・検収部門CSV・月別利用日などの管理系機能が低頻度。`/:token/:id/` で始まるパスは `kyushoku/information/:id/` 等の正規パスが正規化されたもの。

---

## 7. xorder-auth ボトム20

（テーブル30日間総リクエスト数（除外後）: **50,035**）

**注意: このサービスはユニークエンドポイントが13件しかないため、全エンドポイントを表示しています。**

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /user/email/issue-change-url | GET | 1 | 2026-06-11 06:02:49 UTC | メールアドレス変更URL発行（GET） |
| /user/initial-password-reset/check | GET | 1 | 2026-06-10 10:21:45 UTC | 初期パスワードリセットチェック（GET） |
| /user/action_verification/signup/ | GET | 2 | 2026-05-26 00:27:49 UTC | サインアップ検証（トークンなし） |
| /user/password | PUT | 14 | 2026-06-19 05:37:19 UTC | パスワード変更 |
| /user/password/reset | PUT | 19 | 2026-06-19 04:28:32 UTC | パスワードリセット実行 |
| /user/email | PUT | 20 | 2026-06-20 01:46:37 UTC | メールアドレス変更 |
| /user/action_verification/password-reset/:token | GET | 24 | 2026-06-19 04:28:19 UTC | パスワードリセットトークン検証 |
| /user/email/issue-change-url | POST | 40 | 2026-06-20 01:40:59 UTC | メールアドレス変更URL発行 |
| /user/password/issue-reset-url | POST | 105 | 2026-06-19 07:49:19 UTC | パスワードリセットURL発行 |
| /user | POST | 327 | 2026-06-20 06:11:44 UTC | ユーザー登録 |
| /user/action_verification/signup/:token | GET | 673 | 2026-06-21 04:23:57 UTC | サインアップトークン検証 |
| /user/initial-password-reset/check | POST | 2,937 | 2026-06-21 15:11:47 UTC | 初期パスワードリセットチェック |
| /user/service | GET | 45,872 | 2026-06-21 14:55:52 UTC | サービス情報取得 |

> **所見:** API面が非常に小さい（13エンドポイント）。トラフィックの91.7%が `/user/service GET` に集中。パスワード変更系（PUT）が月14〜19回と極めて低頻度。

---

## 8. xorder-auth-internal ボトム20

（テーブル30日間総リクエスト数（除外後）: **38,773**）

**注意: このサービスはユニークエンドポイントが3件しかないため、全エンドポイントを表示しています。**

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /user/emails/search | POST | 554 | 2026-06-20 07:01:32 UTC | メールアドレス検索 |
| /user/pre-signup | POST | 833 | 2026-06-20 07:30:17 UTC | プレサインアップ |
| /:token | GET | 37,386 | 2026-06-21 14:55:53 UTC | トークン検証（正規化済み） |

> **所見:** 内部APIのため3エンドポイントのみ。96.4%が `/:token GET`（実際は `/user/service/verify` 等の長いパスが正規化されたもの）。

---

## 9. xorder-api 請求書系 (/invoice) ボトム20

（テーブル30日間 /invoice 総リクエスト数（除外後）: **64,118**）

| endpoint | http_method | call_count_30d | last_called_at | notes |
|---|---|---|---|---|
| /invoice/suppliers/:id/shops/012532-00/lines | GET | 1 | 2026-06-01 06:31:33 UTC | 店舗コード未正規化 |
| /invoice/suppliers/:id/shops/3715-10/lines | GET | 1 | 2026-06-02 07:30:54 UTC | 同上 |
| /invoice/suppliers/:id/shops/G3267/lines | GET | 1 | 2026-06-01 10:22:24 UTC | 同上 |
| /invoice/suppliers/:id/shops/1889-01/lines | GET | 1 | 2026-06-02 07:55:18 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0266/lines | GET | 1 | 2026-06-01 09:15:39 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0578/lines | GET | 1 | 2026-06-03 07:04:59 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0786/lines | GET | 1 | 2026-06-05 07:01:39 UTC | 同上 |
| /invoice/suppliers/:id/shops/060187-00/lines | GET | 1 | 2026-06-01 06:32:46 UTC | 同上 |
| /invoice/suppliers/:id/shops/026161-00/lines | GET | 1 | 2026-06-01 06:32:01 UTC | 同上 |
| /invoice/suppliers/:id/shops/2162-04/lines | GET | 1 | 2026-06-02 07:55:38 UTC | 同上 |
| /invoice/suppliers/:id/shops/3715-06/lines | GET | 1 | 2026-06-02 07:30:52 UTC | 同上 |
| /invoice/suppliers/:id/shops/6029-02/lines | GET | 1 | 2026-06-10 08:02:26 UTC | 同上 |
| /invoice/suppliers/:id/shops/3415-06/lines | GET | 1 | 2026-06-02 07:30:47 UTC | 同上 |
| /invoice/suppliers/:id/shops/take002/lines | GET | 1 | 2026-06-01 04:11:40 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0962/lines | GET | 1 | 2026-06-01 09:10:49 UTC | 同上 |
| /invoice/suppliers/:id/shops/N0014/lines | GET | 1 | 2026-06-05 02:11:54 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0576/lines | GET | 1 | 2026-06-03 07:04:13 UTC | 同上 |
| /invoice/suppliers/:id/shops/7034-0/lines | GET | 1 | 2026-05-26 02:59:44 UTC | 同上 |
| /invoice/suppliers/:id/shops/N0033/lines | GET | 1 | 2026-06-01 02:34:25 UTC | 同上 |
| /invoice/suppliers/:id/shops/G0950/lines | GET | 1 | 2026-06-01 09:10:38 UTC | 同上 |

> **所見:** ボトム20が全件 `/invoice/suppliers/:id/shops/{shop_code}/lines` パターン。店舗コード（`G3267`, `3715-10`, `012532-00`, `take002` 等）がパスパラメータとして埋め込まれており、正規化ルールで吸収できていない。これらを `/invoice/suppliers/:id/shops/:shop_code/lines` として正規化すれば1つのエンドポイントに集約され、実コール数は64,118件中の大部分を占めると推定される。**invoice系は実質的に低頻度エンドポイントを持たない可能性が高い。**
