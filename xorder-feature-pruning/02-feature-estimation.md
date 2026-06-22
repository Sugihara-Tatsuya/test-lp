# Phase 2: xOrder ボトム20エンドポイント 機能推定結果

Devin セッション: [devin-3c430384f86b4bd39eb59db22f2cedce](https://app.devin.ai/sessions/3c430384f86b4bd39eb59db22f2cedce)
取得日時: 2026-06-21 22:48:56 UTC（最終出力）

---

## 調査メモ

- **Group A (#1-#10)**: xmart-web-api のViewSet/URL定義から特定。フロントはxmart-web-supplier-ordering/xmart-web-shop-ordering。
- **Group B (#11-#26)**: 旧Djangoアドミン（xmart-web-admin）のページURL。**指定4リポには含まれない**ため、xmart-web-api のモデル名やxmart-web-admin-ordering の新画面から推定。
- **Group C (#27-#30)**: xmart-web-supplier-ordering のNuxt 2ページURL。#28, #30 は4リポ内に該当コードなし。
- **Group D (#31-#36)**: xorder-kyushoku-api（FastAPI）のルーター定義から特定。指定4リポ外だがマシン上に存在したため調査実施。

---

## 機能推定テーブル

| # | endpoint | http_method | call_count_30d | service | repository | feature_category | feature_name | frontend_page_path | notes |
|---|----------|-------------|----------------|---------|------------|-----------------|-------------|-------------------|-------|
| 1 | /collection/route | POST | 1 | xorder-api | xmart-corp/xmart-web-api | その他(回収) | 回収ルート作成 | supplier: /dealshops/collection/ | `CollectionRouteViewSet` (CreateModelMixin)。空瓶等の回収ルートを新規作成 |
| 2 | /collection/shop-supplier/group | POST | 1 | xorder-api | xmart-corp/xmart-web-api | その他(回収) | 回収グループ作成 | supplier: /dealshops/collection/ | `ShopCollectionSupplierGroupViewSet`。卸-飲食店間の回収グループを新規作成 |
| 3 | /supplier_order/me/v2/catalogs/:id | DELETE | 1 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | カタログV2削除 | supplier: /catalog/list/ | `SupplierCatalogV2ViewSet` (DestroyModelMixin)。カタログの物理削除 |
| 4 | /supplier_order/me/supplier-user-csv/upload/template_csv | GET | 1 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | ユーザー登録CSVテンプレートDL | supplier: /supplier_users/ | `SupplierUserCSVHistoryViewSet.template_csv`。新規ユーザー登録用CSVテンプレートをダウンロード |
| 5 | /supplier_order/me/shops/:id/products_v2/undefined | GET | 5 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | 取引先商品一覧V2（バグ） | supplier: /dealshops/shop/products/ | フロントで商品IDがundefinedのままAPIコール。フロントのバグ |
| 6 | /shop_order_supplier/:id/subscription_delivery/info/:id/read | PUT | 5 | xorder-api | xmart-corp/xmart-web-api | 定期配送 | 定期納品お知らせ既読 | shop: 定期納品画面 | `ShopSubscriptionDeliveryOrderInfoViewSet.read`。お知らせを既読にするカスタムアクション |
| 7 | /supplier_order/me/subscription_delivery/:id/schedule/:id/update_quantity | PUT | 5 | xorder-api | xmart-corp/xmart-web-api | 定期配送 | 定期納品スケジュール数量更新 | supplier: /subscription-delivery/ | `SubscriptionDeliveryOrderScheduleViewSet.update_quantity`。定期納品スケジュールの数量を変更 |
| 8 | /supplier_order/me/catalog-record/bulk_file_upload_template_csv | GET | 5 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | カタログ掲載商品一括更新CSVテンプレートDL | supplier: /catalog/list/ | `SupplierCatalogRecordViewSet.bulk_file_upload_template_csv` |
| 9 | /supplier_order/me/shop-code-map | GET | 5 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | 取引先コード変換マップ一覧 | supplier: /dealshops/shop-code-conversion/ | `SupplierShopCodeMapViewSet`。ページネーション付き一覧取得 |
| 10 | /operator/suppliers/:id/shop-group-csv | GET | 5 | xorder-api | xmart-corp/xmart-web-api | マスタ管理 | 取引先グループCSV DL | admin: /supplier/[id]/shop/ | `OperatorOrderShopGroupCSVViewSet`。admin-orderingのsupplierShopGroupCSV storeから呼出 |
| 11 | /suppliers/:id/order-settings/split/:id/delete/ | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 受発注 | 注文分割設定 削除確認 | legacy admin画面 | `SupplierOrderSplitSetting`モデルの削除確認ページ。注文を条件(SQLクエリ)で自動分割する設定の削除 |
| 12 | /ordering/suppliers/:id/shop_collection/setting/:id | GET/POST | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | その他(回収) | 回収グループ設定 | legacy admin画面 | 回収機能の飲食店グループ設定ページ（作成/編集） |
| 13 | /order_supplier/:id/share_email/:id/update | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 通知 | 担当区分メーリス更新 | legacy admin画面 | 注文通知の共有メールアドレス(担当区分)の更新ページ |
| 14 | /supplier/:id/order_plan/this-month/delete | GET/POST | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | マスタ管理 | 今月の受発注プラン削除 | legacy admin画面 | 卸の今月分の受発注プランを削除。admin-orderingにSupplierDetailViewで同等機能あり |
| 15 | /:token/:id/products-csv/:id/download/error_upload_csv | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 連携 | 商品CSVエラーCSV DL | legacy admin画面 | 商品CSVアップロード時のバリデーションエラーCSVダウンロード。tokenベースのアクセス |
| 16 | /order_option_plan/update/:id | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | マスタ管理 | オプションプラン更新 | legacy admin画面 | 受発注オプションプラン(FTP/Voice/FAX等の付加機能)の更新ページ |
| 17 | /ordering/suppliers/:id/price-csv/unit-splitter-setting | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 連携 | 単価CSV単位分割設定 | legacy admin画面 | 単価CSVインポート時の単位分割ルール設定。API側は`PriceMasterSplitterSettingAPIView` |
| 18 | /suppliers/:id/order-settings/tag/:id/delete/ | POST | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 受発注 | 注文タグ設定 削除 | legacy admin画面 | `SupplierOrderTagSetting`モデルの削除実行。注文に自動タグ付けするルールの削除 |
| 19 | /api/operator/order/:id/pdf/download | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-api | レポート | 注文書PDFダウンロード | legacy admin画面 | `SupplierOrderPdfDownloadViewSet`。API実体はxmart-web-api。admin-legacyが`/api/`プレフィックスでプロキシ |
| 20 | /ordering/suppliers/:id/shops/relation/:id/password | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 認証 | 取引先パスワード設定 | legacy admin画面 | 卸の取引先（飲食店）に紐づくログインパスワードの設定/確認ページ |
| 21 | /ordering/suppliers/:id/records/:id/delete | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 受発注 | 注文レコード削除確認 | legacy admin画面 | 注文明細レコードの削除確認ページ |
| 22 | /claim/:id | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | レポート | 請求書詳細 | legacy admin画面 | 請求書の詳細表示ページ |
| 23 | /ordering/suppliers/:id/shop_collection/create | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | その他(回収) | 回収グループ作成 | legacy admin画面 | 回収グループの新規作成ページ |
| 24 | /supplier/:id/ftp | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 連携 | FTP連携設定 | admin-ordering: /supplier/[id]/ftp | FTP連携(受注CSVの自動配信)設定。新admin-orderingにも同画面あり(pages/supplier/[id]/ftp.vue) |
| 25 | /ordering/suppliers/:id/catalog-product-master-csv/unit-splitter-setting | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | 連携 | カタログ商品マスタCSV単位分割設定 | legacy admin画面 | カタログ商品マスタCSVインポート時の単位分割設定。API側は`CatalogProductUnitSplitterSettingAPIView` |
| 26 | /ordering/suppliers/:id/flyer/product | GET | 1 | xorder-admin-legacy | xmart-corp/xmart-web-admin (対象外) | マスタ管理 | チラシ商品管理 | legacy admin画面 | チラシ掲載商品の管理ページ(チラシに載せる商品の設定) |
| 27 | /order/history-deadline/shops/ | GET | 1 | xorder-supplier | xmart-corp/xmart-web-supplier-ordering | 受発注 | 注文履歴 締切別 店舗一覧 | supplier: /order/history-deadline/shops/ | `pages/order/history-deadline/shops/index.vue`。締切日ごとの店舗別注文履歴一覧ページ |
| 28 | /member/agree | GET | 1 | xorder-supplier | unknown | 認証 | 利用規約同意(推定) | 不明 | 4リポ内に該当コードなし。利用規約同意ページと推定。レガシーまたは削除済みルートの可能性 |
| 29 | /dealshops/delivery_group/specified/edit | GET | 1 | xorder-supplier | xmart-corp/xmart-web-supplier-ordering | マスタ管理 | 個別配送グループ編集 | supplier: /dealshops/delivery_group/specified/edit | `pages/dealshops/delivery_group/specified/edit.vue`。特定の取引先に対する個別配送グループの編集画面 |
| 30 | /list/discontinued | GET | 1 | xorder-supplier | unknown | マスタ管理 | 販売終了商品一覧(推定) | 不明 | 4リポ内に該当コードなし。販売終了/廃盤商品の一覧ページと推定。レガシーまたは削除済みルートの可能性 |
| 31 | /kyushoku/me/kyushoku-group/csv/:id/fix | POST* | 1 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 施設グループCSV注文確定 | kyushoku-web (対象外) | `fix_kyushoku_group_csv_order`。注文確定処理またはkyushoku別CSV注文作成。*BQログはGETだが実際はPOST |
| 32 | /admin/supplier-product-matching/:id | DELETE | 1 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 突合事前学習レコード削除 | admin-ordering: 突合事前学習画面 | `AdminSupplierProductMatchingService.delete`。給食CSV商品マッチングの事前学習レコードを物理削除 |
| 33 | /kyushoku/me/kyushoku-group/:id/csv/order/products/delivery-date | PUT | 1 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 施設グループCSV注文 納品日一括更新 | kyushoku-web (対象外) | `bulk_update_kyushoku_group_csv_order_product_delivery_date_v2`。複数CSV注文商品の納品日を一括変更 |
| 34 | /admin/kyushoku/:id/csv/:id/error | GET | 1 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 管理者向けCSVエラー取得 | admin-ordering: 給食管理画面 | `AdminKyushokuCSVService.get_csv_error`。CSVアップロード時のバリデーションエラー情報を取得 |
| 35 | /kyushoku/me/orders/:id/inspection-department-csv | GET | 7 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 検収表CSV(部門別) DL | kyushoku-web: 注文詳細画面 | `OrderDownloadService.get_inspection_department_csv`。部門対応の検収表をCSVでダウンロード |
| 36 | /suppliers/me/proxy-order/csv/columns | POST | 8 | xorder-kyushoku | xorder-kyushoku-api | 給食 | 代理注文CSVカスタム項目更新 | supplier-ordering (対象外) | `ProxyOrderCSVColumnService`。卸が代理注文CSVのカスタム項目(列)設定を更新 |
