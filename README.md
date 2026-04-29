# Godavari Cincinnati QR Menu

This is a GitHub Pages-ready QR menu website for Godavari Cincinnati.

## How it works

- Customers scan one permanent QR code.
- The QR code opens the GitHub Pages menu website.
- Owners update the menu in Google Sheets.
- The website reads the published Google Sheet CSV and hides unavailable items.

## Files

- `index.html` - menu page
- `style.css` - Godavari-style red, gold, and cream theme
- `script.js` - loads and renders menu data
- `assets/godavari-logo.jpeg` - logo
- `data/sample-menu.csv` - fallback/sample menu format

## Google Sheet columns

Use this exact header row:

```csv
Category,Item Name,Description,Price,Veg/Non-Veg,Spice Level,Available,Popular,Sort Order
```

Recommended values:

- `Available`: Yes or No. Items marked No are hidden from customers.
- `Popular`: Yes or No.
- `Price`: number only, for example `12.99`.
- `Sort Order`: lower numbers show first.

## Connect Google Sheets

1. Create a Google Sheet with the exact columns above.
2. Share it with all owners who need to edit the menu.
3. In Google Sheets, go to File > Share > Publish to web.
4. Choose the menu sheet and publish as CSV.
5. Copy the published CSV link.
6. Open `script.js`.
7. Replace this line:

```js
const MENU_CSV_URL = "data/sample-menu.csv";
```

with your published Google Sheet CSV URL:

```js
const MENU_CSV_URL = "YOUR_GOOGLE_SHEET_PUBLISHED_CSV_URL_HERE";
```

## GitHub Pages setup

1. Create a new GitHub repository, for example `godavari-cincinnati-menu`.
2. Upload these files to the repository.
3. Go to Settings > Pages.
4. Under Build and deployment, choose Deploy from a branch.
5. Select branch `main` and folder `/root`.
6. Save.
7. Your menu URL will look like:

```text
https://YOUR-GITHUB-USERNAME.github.io/godavari-cincinnati-menu/
```

## QR code

Generate the QR code after GitHub Pages is live. Use the GitHub Pages URL. Do not generate QR codes for individual menu files or Google Sheet links.

## Editing menu later

Owners only edit the Google Sheet. No GitHub editing is needed after setup unless you want design changes.
