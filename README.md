# אין שאלות טיפשיות על אופניים

סוכן שמנהל עמוד אינסטגרם וטיקטוק כמעט לבד, ולוח בקרה ("מחברת המעבדה") שמראה מה הוא עשה ומה מחכה לך.
ההקשר המלא לפרויקט נמצא ב־`CLAUDE.md`.

## מבנה
```
site/            לוח הבקרה (HTML סטטי)
functions/api/   שמירת הצ'קליסט (Cloudflare Pages Function)
data/            כל המצב של הסוכן, כקבצי JSON
engine/          סקריפטי הסוכן (בבנייה)
.github/         תזמונים ב־GitHub Actions (בבנייה)
```

## הקמת לוח הבקרה ב־Cloudflare Pages (פעם אחת, כ־10 דקות)
1. ב־Cloudflare: **Workers & Pages ← Create ← Pages ← Connect to Git**, ובוחרים את הריפו.
2. הגדרות build:
   - Build command: `mkdir -p site/data && cp data/*.json site/data/`
   - Build output directory: `site`
3. **Settings ← Variables and Secrets**, מוסיפים:
   - `GITHUB_REPO` = `oschmidek-collab/no-stupid-questions`
   - `GITHUB_TOKEN` = טוקן מסוג fine-grained מ־GitHub (Settings ← Developer settings ← Personal access tokens ← Fine-grained), עם גישה **רק** לריפו הזה והרשאת **Contents: Read and write**. מסמנים אותו כ־Secret.
4. **נעילה:** Zero Trust ← Access ← Applications ← Add ← Self-hosted. הדומיין של האתר, ומדיניות Allow רק לכתובת המייל שלך. מעכשיו הכניסה לאתר היא בקוד חד־פעמי למייל.
5. Deploy. כל commit לריפו מעדכן את האתר אוטומטית.

## פיתוח מקומי
פותחים את `site/index.html` דרך שרת סטטי שמגיש גם את `data/`. בלי השרת של Cloudflare, סימוני הצ'קליסט נשמרים רק בדפדפן.
