# אין שאלות טיפשיות על אופניים — הקשר לפרויקט

סוכן אוטונומי שמנהל עמוד אינסטגרם וטיקטוק בעברית על אופניים, כניסוי: כמה עמוד שמופעל כמעט בלי יד אדם יכול לגדול ב־90 יום.

תנ"ך המותג והתוכן (הקונספט, הטון, הסדרות, הכללים): https://claude.ai/artifact/1dZTaf5F53hVVBHSk2wk71
כל החלטת תוכן חייבת להתיישב איתו.

## הקונספט בשורה
תשובות רציניות לשאלות טיפשיות, ותשובות פשוטות לשאלות רציניות. הומור יבש (deadpan), לעולם לא על חשבון השואל. כל פוסט: שורה ראשונה למתחיל, שכבה עמוקה למקצוען.

## ארכיטקטורה
| שכבה | מה | איפה |
| --- | --- | --- |
| מוח שבועי | ניתוח ביצועים, תוכנית שבועית, עדכון `data/plan.json` ו־`data/decisions.json` | משימה מתוזמנת של Claude |
| מנוע יומי | ייצור תוכן, פרסום, מענה לתגובות, משיכת נתונים | `engine/` + GitHub Actions |
| מוח יומי | ניסוח כיתובים ותגובות | Gemini Flash (API חינמי) |
| לוח בקרה | צ'קליסט, תור תוכן, שאלות, צמיחה, יומן החלטות | `site/` כ־Cloudflare Worker עם static assets, מאחורי Cloudflare Access |
| שרת לוח הבקרה | מגיש את `data/*.json` חי מהריפו, ושומר סימוני צ'קליסט כ־commit | `worker.js` + `wrangler.jsonc` |

כל המצב נשמר כקבצי JSON בתיקייה `data/`. הריפו הוא מקור האמת היחיד.

## קבצי נתונים
- `tasks.json` — משימות אנושיות: `{id, date, type: like|comment|follow|publish|create|review, url, instruction, text?, done}`
- `queue.json` — תור תוכן: `{id, date, platform, series, title, status: idea|ready|scheduled|posted|failed, permalink?}`
- `questions.json` — שאלות מעוקבים: `{id, received, text, level: beginner|regular|pro, status: new|planned|answered}`
- `metrics.json` — `{daily: [{date, ig_followers, tt_followers, reach, saves, shares}]}`
- `decisions.json` — יומן: `{week, change, reason, result?}`

## כללי ברזל
1. אין פעולות אוטומטיות בחשבונות של אחרים. לייקים, עקיבות ותגובות בחוץ הולכים ל־`tasks.json`, עד 10 דקות ביום.
2. תוכן AI מסומן כך בפלטפורמה.
3. אין העלאה של תוכן של אחרים. רק תוכן מקורי וחומרים ברישיון חופשי (Pexels, OpenStreetMap) עם קרדיט.
4. כל עובדה נבדקת מול מקור. אין מקור? לא מפרסמים.
5. לא צוחקים על השואל. שאלות מתפרסמות באנונימיות.
6. בלי פוליטיקה, בלי ייעוץ רפואי.
7. משתנה אחד בשבוע, מתועד ב־`decisions.json`.
8. אירוע חריג (תגובה פוגענית, ויראליות, פנייה מסחרית) → עוצרים ומוסיפים משימת `review`.

## מוסכמות קוד
- האתר: HTML/CSS/JS סטטי בלי build, עברית, RTL, mobile-first.
- צבעים: רקע #F5F1E8, טקסט #1A1A1A, כתום #FF5A1F, כחול #1F4E8C. גופנים: Heebo, Assistant, IBM Plex Mono.
- סודות רק ב־GitHub Secrets / Cloudflare (Worker → Settings → Variables and Secrets), אף פעם לא בקוד.
- כל push ל־main מפרסם את לוח הבקרה מחדש אוטומטית (Workers Builds).
