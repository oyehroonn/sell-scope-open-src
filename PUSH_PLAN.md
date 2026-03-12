# Why one `apps` folder? + Push plan (folder-by-folder, under 100 MB)

## Why one `apps` folder?

There is **one** folder called `apps`, and inside it you have **two applications**:

- `apps/web` — Next.js frontend
- `apps/api` — FastAPI backend

So it’s not “two apps folders”; it’s **one `apps` folder that holds multiple apps**. This is a standard **monorepo** layout:

- Keeps the repo root clean (one place for all “applications”).
- Tools like pnpm workspaces and Turbo use `apps/*` to find and build each app.
- Root `package.json` and `pnpm-workspace.yaml` refer to `apps/*` so you can run everything from the root.

You could rename `apps` to something like `projects` or `services`, but the structure would stay: one parent folder, multiple app subfolders.

---

## Push plan: add folders one by one (each under 100 MB)

GitHub warns on files over 100 MB. With `.gitignore` in place, **node_modules**, **venv**, **.next**, and **scraper/output** are not added, so each folder you add stays small (well under 100 MB).

Do everything inside your repo folder (e.g. `sell-scope-open-src`):

```bash
cd sell-scope-open-src
git remote -v   # should point to sell-scope-open-src on GitHub
```

Then add and push **one logical “folder” at a time** (order is flexible; this order keeps root and config first):

### 1. Root config and docs (no big folders)

```bash
git add .gitignore README.md LICENSE package.json pnpm-workspace.yaml turbo.json docker-compose.yml docker-compose.dev.yml PUSH_PLAN.md
git add docs/
git status   # check nothing huge is staged
git commit -m "chore: root config, docs, and push plan"
git push
```

### 2. `apps/api` (Python backend; venv ignored)

```bash
git add apps/api/
git status
git commit -m "feat: FastAPI backend (apps/api)"
git push
```

### 3. `apps/web` (Next.js frontend; node_modules ignored)

```bash
git add apps/web/
git status
git commit -m "feat: Next.js frontend (apps/web)"
git push
```

### 4. Scraper

```bash
git add scraper/
git status
git commit -m "feat: Adobe Stock scraper"
git push
```

### 5. Extensions

```bash
git add extensions/
git status
git commit -m "feat: Chrome extension"
git push
```

If you don’t have `scraper` or `extensions` in the repo yet, copy them from the parent SellScope folder into `sell-scope-open-src` first, then run the commands above.

---

## Before the first push: get everything into the repo

Your repo should contain the full project. From the **parent** project folder (SellScope), you can copy anything that’s not yet in the repo:

```bash
# From parent (SellScope), with repo folder named sell-scope-open-src:
cp .gitignore package.json pnpm-workspace.yaml turbo.json docker-compose.yml docker-compose.dev.yml README.md LICENSE sell-scope-open-src/
cp -r docs sell-scope-open-src/
cp -r extensions sell-scope-open-src/
cp -r scraper sell-scope-open-src/
# Optional: refresh apps/web from parent (skip node_modules)
rsync -av --exclude=node_modules --exclude=.next ../apps/web/ sell-scope-open-src/apps/web/
```

Then `cd sell-scope-open-src` and run the push sequence above.

---

## Check size before push

To avoid surprises:

```bash
git add <folder>
git status
du -sh .git/   # repo size after commit will be roughly this
```

If anything is over 100 MB, fix `.gitignore` (e.g. add that folder or pattern) and `git reset` the add, then try again.
