# אין שאלות טיפשיות על אופניים

סוכן שמנהל עמוד אינסטגרם וטיקטוק כמעט לבד, ולוח בקרה ("מחברת המעבדה") שמראה מה הוא עשה ומה מחכה לך.
ההקשר המלא לפרויקט נמצא ב־`CLAUDE.md`.

## מבנה
```
site/            לוח הבקרה (HTML סטטי)
worker.js        שרת קטן: מגיש את data/ חי מהריפו ושומר סימוני צ'קליסט
wrangler.jsonc   הגדרות ה־Worker ב־Cloudflare
data/            כל המצב של הסוכן, כקבצי JSON
```

## הקמת לוח הבקרה ב־Cloudflare (פעם אחת)
1. **Compute ← Workers & Pages ← Create**, ייבוא מ־GitHub ובחירת הריפו. Build command: ריק. Deploy command: `npx wrangler deploy`.
2. טוקן ב־GitHub (Settings ← Developer settings ← Personal access tokens ← Fine-grained): גישה **רק** לריפו הזה, **Contents: Read and write**.
3. ב־Worker: **Settings ← Variables and Secrets ← Add**, סוג **Secret**, שם `GITHUB_TOKEN`, והטוקן כערך. (`GITHUB_REPO` כבר מוגדר ב־`wrangler.jsonc`.)
4. **נעילה:** ב־Worker, **Settings ← Domains & Routes**, ליד `workers.dev` מפעילים **Cloudflare Access**, ומגבילים לכתובת המייל שלך.
5. כל push ל־main מפרסם מחדש אוטומטית. הנתונים עצמם נקראים חי מהריפו, כך שעדכון של הסוכן מופיע מיד, בלי פרסום מחדש.

## פיתוח מקומי
`npx wrangler dev`, עם `GITHUB_TOKEN` בקובץ `.dev.vars` (לא נכנס ל־git).

## פרסום לאינסטגרם
- `engine/publish_ig.py` מרנדר פוסט ל־JPEG תחת `media/<id>/`, מחכה שהתמונות יהיו ציבוריות, ומפרסם קרוסלה.
- `.github/workflows/publish-instagram.yml` רץ כל יום ב־18:07 ומפרסם את הפוסט הבא שמועדו הגיע (`status: ready` ב־`data/queue.json`). אפשר להריץ ידנית מ־Actions עם מזהה פוסט.
- Secret ב־GitHub: `IG_ACCESS_TOKEN` (טוקן ארוך טווח, 60 יום).
- התמונות מוגשות לאינסטגרם מ־Worker ציבורי נפרד, `nsq-media` (הקוד ב־`media-worker/worker.js`), עם Secret בשם `GITHUB_TOKEN` (טוקן fine-grained לקריאה בלבד). לוח הבקרה נשאר נעול כולו.
