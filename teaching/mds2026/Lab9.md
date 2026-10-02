# Lab 9

At https://github.com/hcheval/rssmds there is a small implementation of an [RSS](https://en.wikipedia.org/wiki/RSS) feed reader that runs in the terminal, stores entries in SQLite, and includes a web interface (about 1300 lines of Python across 8 modules).

Clone the repository, set up the environment, and make sure both the tests and the type checker pass before moving on. Then try the app out:

```bash
python -m rssmds add "https://hnrss.org/newest?count=5"
python -m rssmds add "https://blog.rust-lang.org/feed.xml"
python -m rssmds fetch
python -m rssmds list
python -m rssmds read 1
python -m rssmds stats
python -m rssmds serve   # open http://127.0.0.1:8080
```


The point of the lab is to navigate and modify the codebase at first encounter using a coding agent. You can use `opencode` for this as in previous labs, or whatever tool you prefer.

## Exercise 1

Answer the following by reading the source code.

1. What happens when `rssmds add` is called with a URL that already exists in the database? Trace the path from the CLI entry point through to the database layer.

2. The fetcher avoids re-downloading feeds that haven't changed since the last fetch. What HTTP mechanism does it use, and which function implements it?

3. The `discover` command tries several strategies to find feeds on a webpage. List them in the order they are attempted and explain when each one kicks in.

4. Use the coding agent to generate a [Mermaid](https://mermaid.js.org/) sequence diagram for the `rssmds fetch` flow. It should start from the CLI dispatch and end with entries stored in the database, covering both the case where the feed has new content and the case where the server returns a 304. Read the generated diagram against the code and fix anything that might be mismatched. To render and edit the diagram, [Mermaid Live Editor](https://mermaid.live) works in the browser with no setup.


## Exercise 2

Pick one of the features below, or propose one of your own as long as it touches at least two modules. Write a short specification (a paragraph is enough) and then use the coding agent to implement it. Once the agent produces code:

- Verify it works by running the app.
- Run `pytest` and make sure the existing tests still pass.
- Write at least 3 tests for the new feature, covering the normal path and an edge case or two.
- Run `mypy rssmds/ --strict` and fix any type errors the agent introduced.
- Read the diff. Check for anything the agent got wrong.

Possible features:

- **Search.** `rssmds search "keyword"` searches entry titles and summaries, displaying results in the same format as `list`. This requires a new query in `db.py` and a new subcommand in `cli.py`, with an optional search bar in `web.py`.

- **Star/bookmark entries.** `rssmds star 42` bookmarks an entry and `rssmds starred` lists all bookmarked entries. This requires a schema change in `db.py` (a new column or table) along with new CLI subcommands, and optionally a star button in the web UI.

- **OPML import.** `rssmds import feeds.opml` parses an [OPML](https://en.wikipedia.org/wiki/OPML) file and subscribes to all feeds in it. Since the export side already exists (`rssmds export opml`), import is the natural complement, requiring a new CLI subcommand and a parser for the OPML format.

- **Purge old entries.** `rssmds purge --older-than 30d` deletes entries older than a threshold. The database function `db.purge_entries` already exists but has no CLI command, and the date arithmetic for parsing "30d" into a cutoff date is missing.

- **Feed categories.** `rssmds add --category tech "https://..."` assigns a category and `rssmds list --category tech` filters by it. This requires a schema change, modifications to the `add` and `list` commands, and ideally filtering in the web UI as well.
