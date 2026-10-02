# Lab 12: Spec-Driven Development

Spec-driven development means writing a structured specification of what a change should do before any code is generated, so that the AI implements against that spec rather than improvising from a loose prompt. This lab uses [OpenSpec](https://github.com/Fission-AI/OpenSpec), a lightweight framework that adds an `openspec/` directory to a repo containing project descriptions, specifications, and change proposals, and that works with any AI coding tool.

We will work with a small CLI task manager (`cli.py`) that reads and writes `tasks.json`. Three commands exist already (`add`, `list`, `complete`), and a fourth, `delete`, is stubbed out. The task is to implement delete with archiving, so that deleted tasks move to `archive.json` rather than disappearing.

The interesting part is everything that one-line description leaves open: what should happen when someone deletes a nonexistent ID, what fields the archive entry should contain, whether task IDs get reused after deletion, and whether archiving preserves the original timestamp or adds a new one. Without a spec to pin these decisions down, a model will resolve all of them silently, possibly inconsistently across runs.


## Setup

Start by installing OpenSpec:

```bash
npm i -g @fission-ai/openspec@latest
```

Download the starter files (`cli.py`), place them in a folder, and initialize a git repo along with OpenSpec:

```bash
git init && git add -A && git commit -m "initial"
openspec init
```

Once that is done, open the project in OpenCode and switch to a free model with the `/model` command (e.g. `glm-4.7`, `minimax-2.5`).

OpenSpec works through slash commands typed inside OpenCode rather than from the terminal. The CLI (`openspec init`, `openspec list`) handles project setup, but the actual change workflow happens via `/opsx-propose`, `/opsx-apply`, and so on.


## Spec-Driven

With the project open in OpenCode, run the propose slash command:

```
/opsx-propose implement-delete
```

This creates `openspec/changes/implement-delete/` containing `proposal.md`, `design.md`, `tasks.md`, and a `specs/` subfolder with requirement specs. Read through what the model generated, then open the spec files under `openspec/changes/implement-delete/specs/` to review and edit them. The model will have written some scenarios, but they are likely vague or incomplete, so tighten them into concrete Given/When/Then scenarios that pin down the edge cases from the introduction. For reference, here is what a precise scenario looks like (this one describes the existing `complete` command, not delete):

```
Given tasks.json contains task with id 2 and status "pending"
When I run `python cli.py complete 2`
Then task 2 in tasks.json has status "complete"
And stdout contains "Completed task 2."
```

Write scenarios for delete that are equally specific. Think about what happens on a nonexistent ID, what fields the archive entry should have, what the output messages look like, and whether task IDs can be reused. The more precise the scenarios are, the less room the model has to improvise.

Once the spec is complete, apply it inside OpenCode:

```
/opsx-apply implement-delete
```

After the model generates the implementation, check it against each scenario and note whether it follows the spec faithfully or still invents behaviour where the spec left room.


## Delta Spec

A delta spec describes only what changes relative to an existing spec, using `## ADDED` and `## MODIFIED` sections rather than rewriting everything from scratch. This second change extends the task manager with a `--priority` flag on the `add` command that accepts `low`, `medium`, or `high` (default `medium`), and the `list` command should then show high-priority tasks first.

Propose it inside OpenCode:

```
/opsx-propose add-priority
```

Then edit the specs in `openspec/changes/add-priority/specs/`. This time, structure the spec as a delta: figure out which parts of the change are entirely new (`## ADDED`) and which parts modify existing behaviour (`## MODIFIED`), and write scenarios for each. Think about what happens to tasks that were created before the priority feature existed.

Once the spec is ready, apply it:

```
/opsx-apply add-priority
```
