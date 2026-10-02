# Lab 8: CI/CD with GitHub Actions

When we run tests on our own machines, we rely on whatever Python version happens to be installed, whatever packages have accumulated over time, and our own memory to actually run them before pushing. CI (Continuous Integration) removes all of that: on every push, a freshly provisioned VM (called a runner) pulls the code, installs dependencies from scratch, runs the test suite, and reports pass or fail. Because the runner starts blank every time, a failure in CI is a real failure, not an artifact of someone's local setup.

CD (Continuous Delivery) adds a publishing step after CI passes. In this lab we will use it to deploy a static site to GitHub Pages, which serves HTML at `https://<username>.github.io/<repo>/`.
As a side note, this is a very good way for you to create a personal webpage, if you don't have one already.

The two connect through branch protection: CI prevents bad code from reaching `main`, and CD only deploys from `main`, so by the time the deploy workflow fires, tests have already passed. We will build this pipeline using GitHub Actions, where workflows are defined as YAML files in `.github/workflows/`.


## Exercise 1: "hello world" workflow

Create a new repository on GitHub and clone it locally. Add `.github/workflows/ci.yml`:

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello from $(uname -a)"
      - run: ls -la
```

The `on` field says when the workflow triggers, here on every push and every pull request. `runs-on` picks the runner OS. Each `run` line is a shell command. The `uses` keyword is different: it pulls in a pre-built action published by someone else. We need `actions/checkout@v4` because the runner starts with an empty filesystem, so the repo has to be cloned in explicitly.

Commit and push, then open the Actions tab on GitHub, click into the workflow run, and expand each step to read its log output.



## Exercise 2: running tests in CI

We need something to test. Add two files to the repo root: the code under test and the tests themselves.

`calc.py`:
```python
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("cannot divide by zero")
    return a / b
```

`test_calc.py`:
```python
import pytest
from calc import add, divide

def test_add():
    assert add(2, 3) == 5

def test_divide():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(1, 0)
```

Update `ci.yml` so the runner installs Python and runs pytest:

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest
      - run: pytest -q
```

Commit all three files and push. The workflow should pass with three green tests.

### Test failure

Open `calc.py` and remove the zero check from `divide`, so it looks like this:

```python
def divide(a, b):
    return a / b
```

Commit and push. The workflow should go red: `divide(1, 0)` now raises `ZeroDivisionError` instead of `ValueError`, so `pytest.raises(ValueError)` doesn't catch it, the exception propagates out, and pytest reports the test as errored. Open the failing run's log and find `test_divide_by_zero` to see this.

Put the zero check back, commit, and push. The workflow should go green again. Because the runner is a blank VM, this same failure would reproduce on any machine, which is the point of running tests in CI rather than relying on each developer to run them locally.



## Exercise 3: lint and branch protection

Add a `ruff check .` step to `ci.yml`, before pytest:

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pytest ruff
      - run: ruff check .
      - run: pytest -q
```

Push, and the workflow should still pass since the existing code is clean. At this point CI runs on every push, but nothing prevents anyone from merging broken code into `main`. CI reports failures but doesn't enforce them. Branch protection changes that.

### Setting up branch protection

On GitHub, go to Settings, then Rules, then Rulesets, then "New ruleset" (a dropdown button, click the arrow), then "New branch ruleset." Configure:

- Ruleset name: anything (e.g., "protect main")
- Target branches: add "main"
- Check "Require a pull request before merging"
- Check "Require status checks to pass", then add the `test` job
- Check "Do not allow bypassing the above settings" (otherwise administrators can merge broken code, and the safety net has a hole)

### Testing branch protection

Create a branch locally:

```bash
git checkout -b lint-test
```

Open `calc.py` and add an unused import at the top:

```python
import os
```

Commit and push the branch:

```bash
git add calc.py
git commit -m "add unused import"
git push -u origin lint-test
```

On GitHub, open a pull request from `lint-test` into `main`. CI should run and fail with F401 (unused import), so the merge button stays disabled. Remove the `import os` line, commit, and push to the same branch. This time CI should pass, the merge button unlocks, and we can merge.

Branch protection is what turns CI from a report into a gate. Without it, CI is just advice.



## Exercise 4: CD to GitHub Pages

We now have CI gating `main`. In this exercise we add the other half: a workflow that deploys a static site to GitHub Pages whenever new code lands on `main`.

We need three files: some data to render, a script that turns it into HTML, and a test to verify that the script works.

`data.json`:
```json
[
    {"title": "Dune", "description": "Desert planet, giant worms, spice economics."},
    {"title": "Neuromancer", "description": "Console cowboy jacks into cyberspace."},
    {"title": "Solaris", "description": "Ocean planet that reads minds."}
]
```

Keep 3-5 entries with a `title` and `description` field each.

`build.py`:
```python
import json
import os

def build():
    with open("data.json") as f:
        items = json.load(f)

    lines = []
    lines.append("<html><body>")
    lines.append("<h1>My list</h1>")
    lines.append("<ul>")
    for item in items:
        lines.append(f"  <li><strong>{item['title']}</strong>: {item['description']}</li>")
    lines.append("</ul>")
    lines.append("</body></html>")

    os.makedirs("site", exist_ok=True)
    with open("site/index.html", "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    build()
```

`test_build.py`:
```python
import json
from build import build

def test_titles_appear_in_output():
    build()
    with open("site/index.html") as f:
        html = f.read()
    with open("data.json") as f:
        items = json.load(f)
    for item in items:
        assert item["title"] in html
```

Run `pytest` locally to make sure everything passes before continuing.

### One-time GitHub setup

On GitHub: Settings, then Pages. Under "Build and deployment", set Source to "GitHub Actions."

### The deploy workflow

Add `.github/workflows/deploy.yml`:

```yaml
name: deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python build.py
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

The build job produces `site/index.html`, but the deploy job runs on a different VM and can't access it directly. The handoff goes through an artifact: `upload-pages-artifact` bundles the `site/` directory at the end of the build job, and `deploy-pages` picks it up in the deploy job. The `permissions` block is needed because Pages deployment requires `pages: write` and `id-token: write`, which runners don't have by default.

`deploy.yml` never checks whether CI passed, and doesn't have to. It triggers on pushes to `main`, and the branch protection rule from Exercise 3 prevents code from reaching `main` unless CI has already passed. By the time `deploy.yml` starts, tests and linting have already succeeded, not because the deploy workflow checked, but because there was no other way for the code to get here. Inside `deploy.yml`, the `needs` keyword links the deploy job to the build job. Across workflows, branch protection links `deploy.yml` to `ci.yml`. Those are two different mechanisms doing two different jobs.

All four files (`data.json`, `build.py`, `test_build.py`, `deploy.yml`) need to land on `main` together. If `deploy.yml` isn't part of the commit that reaches `main`, there is no deploy workflow to trigger. Push them all to a branch, open a PR, wait for CI to pass, then merge into `main`.

Once the merge goes through, open the Actions tab. Both `ci` and `deploy` should have run. Click into the `deploy` run and find the Pages URL on the deploy job's summary page (it also appears under Settings, Pages). Open it to see the site.

### Final verification

Open a new branch and add a failing test to `test_build.py`:

```python
def test_broken():
    assert 1 == 2
```

Push the branch and open a PR. CI should fail, the merge button should be blocked, and the live site should stay exactly as it was, because the broken code never reached `main`.

Close the PR without merging and delete the branch. The broken test only existed to prove the gate works.
