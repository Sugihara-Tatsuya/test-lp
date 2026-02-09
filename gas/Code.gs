/**
 * クロスオーダー検定 ランキングAPI
 *
 * セットアップ手順:
 * 1. Google スプレッドシートを新規作成
 * 2. シート名を「ranking」に変更
 * 3. A1:F1 に見出しを入力: name, level, levelLabel, score, total, date
 * 4. 「拡張機能」→「Apps Script」を開く
 * 5. このコードを貼り付けて保存
 * 6. 「デプロイ」→「新しいデプロイ」→ 種類:「ウェブアプリ」
 *    - アクセスできるユーザー: 「全員」
 *    - 実行ユーザー: 「自分」
 * 7. デプロイ後に表示されるURLを certification.html の GAS_URL に設定
 */

const SHEET_NAME = 'ranking';
const MAX_RECORDS = 500;

/**
 * GET: ランキング取得
 * パラメータ: level (beginner | intermediate | advanced)
 */
function doGet(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) return jsonResponse({ error: 'Sheet not found' }, 404);

    const level = e.parameter.level || '';
    const data = getSheetData(sheet);

    let ranking = data;
    if (level) {
      ranking = data.filter(function(row) { return row.level === level; });
    }

    // スコア降順、同スコアなら日付昇順
    ranking.sort(function(a, b) {
      if (b.score !== a.score) return b.score - a.score;
      return new Date(a.date) - new Date(b.date);
    });

    // 上位100件に制限
    ranking = ranking.slice(0, 100);

    return jsonResponse({ ranking: ranking });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

/**
 * POST: スコア保存
 * body: { name, level, levelLabel, score, total, date }
 */
function doPost(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    if (!sheet) return jsonResponse({ error: 'Sheet not found' }, 404);

    const body = JSON.parse(e.postData.contents);

    // バリデーション
    if (!body.name || !body.level || body.score === undefined) {
      return jsonResponse({ error: 'Missing required fields' }, 400);
    }

    // サニタイズ: 名前は最大20文字
    const name = String(body.name).substring(0, 20);
    const level = String(body.level);
    const levelLabel = String(body.levelLabel || '');
    const score = Number(body.score);
    const total = Number(body.total || 10);
    const passed = score >= 7;
    const date = body.date || new Date().toISOString();

    // 追記
    sheet.appendRow([name, level, levelLabel, score, total, date]);

    // 上限超過時は古いレコードを削除
    const lastRow = sheet.getLastRow();
    if (lastRow > MAX_RECORDS + 1) {
      sheet.deleteRow(2); // ヘッダー行の次の行（最も古い）を削除
    }

    return jsonResponse({ success: true, passed: passed });
  } catch (err) {
    return jsonResponse({ error: err.message }, 500);
  }
}

function getSheetData(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return [];

  const range = sheet.getRange(2, 1, lastRow - 1, 6);
  const values = range.getValues();

  return values.map(function(row) {
    return {
      name: row[0],
      level: row[1],
      levelLabel: row[2],
      score: row[3],
      total: row[4],
      date: row[5]
    };
  });
}

function jsonResponse(data, statusCode) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
