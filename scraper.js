name: Update Program List

on:
  schedule:
    - cron: "0 */12 * * *" # runs every 12 hours
  workflow_dispatch:      # allow manual run

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "18"

      - name: Install deps
        run: npm install cheerio node-fetch

      - name: Run scraper
        run: node scraper.js

      - name: Commit changes
        run: |
          git config user.name "GitHub Bot"
          git config user.email "bot@github.com"
          git add index.html
          git commit -m "Auto-update programs" || echo "No changes"
          git push
