# xOrder 機能利用分析プロジェクト

## あなたの役割
このセッションのあなた(Opus)は本プロジェクトの設計・監査・最終判断を担当。
実行作業は原則 Task ツールで Sonnet サブエージェントに委譲してください。

### Sonnetに必ず委譲
- Devinセッション作成・進捗ポーリング・成果物取得
- BQ/GA4等のMCPツール呼び出しと結果整形
- 長文出力の要約、表整形、ファイル読み書き

### あなた(Opus)が必ずやる
- Devin/Sonnetに渡す指示の設計とレビュー
- 各フェーズ完了時の監査(妥当性チェック)
- 機能廃止可否の最終判断
- 例外時の戦略変更
- ユーザー(私)への簡潔な進捗報告と判断材料提示

### 動き方の原則
- 各フェーズ完了時、必ず私の承認を待ってから次へ進む
- 中間進捗の報告は短く、最終成果物の妥当性チェックに集中
- Sonnetへの依頼時は「期待出力フォーマット」を明確に指定

## プロジェクト全体ゴール
xOrder系プロダクト群について、影響の少ない順に機能廃止候補をランク付けし、
最終的に「廃止して良いと判断できる機能トップN」を出す。

## 作業ディレクトリ
~/xorder-feature-audit/ を作業ディレクトリとして使用。
各フェーズの成果物を以下に保存:
- 01-session-alpha-result.md  (BQボトム20)
- 02-session-beta-result.md   (機能意味推定)
- 03-ga4-cross-reference.md   (GA4突き合わせ)
- 04-final-ranking.md         (最終ランク)

---

## Phase 1: ボトム機能の特定 (Devin Session α)

### Opusの判断
以下のDevinセッション用プロンプトをレビュー、必要なら微調整。
ヘルスチェック等の除外条件が業務的に妥当かチェック。

### Sonnetへの依頼内容
"以下のプロンプトでDevinセッションを作成し、完了するまでポーリング(60秒間隔)。
完了したら devin_session_gather で成果物取得し、結果テーブルだけをMarkdownで返してください。
進捗の中間出力は要約せず、最終成果と特筆すべき問題のみ報告。"

### Devinセッションへの指示
タイトル: xOrder 機能利用ボトム20 抽出

タスク内容:
- 接続済みのBigQuery MCPを使い、xmart-corp/xorder-log-to-bigquery が書き込んでいる
  BQテーブル(複数の可能性あり)を特定する
- テーブル特定にあたっては xorder-log-to-bigquery リポを ask_question で
  READMEレベルだけ読む(深追いしない)
- 直近30日のAPIアクセスログから、エンドポイント(http_method + path_pattern)単位で
  コール数を集計
- ヘルスチェック・メトリクス・OPTIONS・静的アセット等の運用系エンドポイントは除外
- call_count >= 1 のうちボトム20件を抽出
- 各行のカラム: endpoint / http_method / call_count_30d / unique_tenants_30d 
  / last_called_at / repository_hint(自明なら)
- 結果はMarkdownテーブルで出力

制約:
- コードリポジトリの深読みは禁止 (BQクエリで完結)
- 1セッション内で完結、サブセッション作成禁止
- ACU上限 5

完了後、結果をセッション内に投稿し終了。

### Phase 1 完了条件
- 01-session-alpha-result.md に結果が保存されている
- Opusが結果を監査済み
- ユーザー(私)に結果と次フェーズ進行可否の判断を求めた

---

## Phase 2: 機能の意味推定 (Devin Session β)

⚠️ Phase 1がユーザー承認された後にのみ実行。

### Opusの判断
Phase 1の20件を見て、Session β プロンプトを設計。
明らかに業務系でない(管理画面・社内APIなど)エンドポイントがあれば対象から除外。

### Sonnetへの依頼内容
"以下のプロンプトでDevinセッションを作成し、完了までポーリング。完了したら
成果物を取得し、Phase 1の表に repository / feature_category / feature_name / 
frontend_page_path / notes の列を追加したMarkdown表として返してください。"

### Devinセッションへの指示
タイトル: xOrder ボトム20 機能意味推定

タスク内容:
[Phase 1の20件の表をここに貼り付け]

上記20件それぞれについて、xorder-* リポ群(list_available_repos で取得)を
ask_question で読み、以下を埋める:
- repository: 該当するリポジトリ名 (xmart-corp/xorder-xxx)
- feature_category: 大分類 (受発注/マスタ管理/通知/認証/連携/レポート/その他)
- feature_name: 機能名の推定 (推測でOK、自信度低い場合はその旨記載)
- frontend_page_path: 関連するフロントエンドページがあれば (xmart-web-*リポも参照)
- notes: 補足、判定難易度、コメント

制約:
- 各エンドポイントにつき ask_question 呼び出しは最大3回まで
- 推定不能なものは "unknown" として理由を記載
- 1セッション完結、ACU上限 10
- 出力は Markdown テーブル

### Phase 2 完了条件
- 02-session-beta-result.md に保存
- Opusが推定の妥当性を監査
- ユーザーに結果と次フェーズ進行可否の判断を求めた

---

## Phase 3: GA4データ統合

⚠️ Phase 2がユーザー承認された後にのみ実行。

### 前提確認
このClaude Code環境に ga4-xorder / ga4-xorder-supplier のMCPが
接続されているか確認。`claude mcp list` で確認可。
なければユーザーに接続を依頼してから進む。

### Opusの判断
Phase 2の20件のうち frontend_page_path が判明したものとそうでないものを分ける。
判明しているものはGA4突き合わせ、不明なものは「バックエンドのみ機能」として
別カテゴリ扱い。

### Sonnetへの依頼内容
"Phase 2の結果を受け、以下を実行:

a) ga4-xorder, ga4-xorder-supplier MCPで直近30日のページ別メトリクス取得
   - 各pagePathについて screenPageViews, totalUsers, sessions
b) Phase 2のテーブルに以下の列を追加:
   - ga4_pv_30d
   - ga4_unique_users_30d
   - ga4_sessions_30d
   - ga4_status: matched / not_matched / no_page_mapped
c) frontend_page_path が複数のGA4 propertyに跨る場合は両方確認し合算
d) 結果テーブルを 03-ga4-cross-reference.md に保存
e) Opusに結果サマリーを返す(全表は返さず、特筆事項とハイライト件数のみ)"

### Phase 3 完了条件
- 03-ga4-cross-reference.md 保存済
- Opusが対応妥当性を監査
- 「APIコール少・PV少」「APIコール少・PV多」「APIコール少・GA4対応なし」の
  3グループに分類できている
- ユーザーに結果報告

---

## Phase 4: 廃止候補の最終ランク付け

⚠️ Phase 3がユーザー承認された後にのみ実行。

### Opusが直接実行(委譲せず)
Phase 1-3の全結果を統合し、以下の5軸で各候補を評価。
各5点満点、合計25点で降順ソート:

- Coverage: unique_tenants 少ないほど高得点 (廃止しやすい)
- Volume: call_count 少なく減少傾向なら高得点
- Frontend: ga4_pv 少 or 対応なしなら高得点
- Mapping Confidence: 機能推定の自信度が高いほど高得点
- Risk Inverse: 認証/決済/通知/契約等の重要ドメインに該当しないほど高得点

上位10件について 04-final-ranking.md にレポート作成。各行に:
- エンドポイント・推定機能・各軸スコア・合計点
- 廃止判断時に確認すべき追加質問 (誰に聞く・何を見る)
- 想定リスク
- 推奨アクション: 即廃止可 / 要調査 / 要顧客通知 / 廃止非推奨

### Phase 4 完了条件
- 04-final-ranking.md にトップ10レポート保存
- Opusがユーザーに最終レポートを提示し、廃止判断を仰いだ

---

ではPhase 1から開始してください。
まず ~/xorder-feature-audit/ を作成し、`claude mcp list` で
GA4関連MCPの接続状況を確認し、私に状況報告した上でPhase 1のDevinセッション設計に進んでください。