import argparse
import json
from datetime import datetime, timezone

TASKS_FILE = "tasks.json"
ARCHIVE_FILE = "archive.json"


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def next_id(tasks):
    return max((t["id"] for t in tasks), default=0) + 1


def cmd_add(args):
    tasks = load(TASKS_FILE)
    task = {
        "id": next_id(tasks),
        "title": args.title,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tasks.append(task)
    save(TASKS_FILE, tasks)
    print(f"Added task {task['id']}: {task['title']}")


def cmd_list(args):
    tasks = load(TASKS_FILE)
    if not tasks:
        print("No tasks.")
        return
    for t in tasks:
        mark = "x" if t["status"] == "complete" else " "
        print(f"  [{mark}] {t['id']}. {t['title']}")


def cmd_complete(args):
    tasks = load(TASKS_FILE)
    for t in tasks:
        if t["id"] == args.id:
            t["status"] = "complete"
            save(TASKS_FILE, tasks)
            print(f"Completed task {args.id}.")
            return
    print(f"Task {args.id} not found.")


def cmd_delete(args):
    try:
        tasks = load(TASKS_FILE)
    except FileNotFoundError:
        print("No tasks to delete.")
        return

    if not tasks:
        print("No tasks to delete.")
        return

    for i, t in enumerate(tasks):
        if t["id"] == args.id:
            del tasks[i]
            save(TASKS_FILE, tasks)
            print(f"Deleted task {args.id}.")
            return

    print(f"Task {args.id} not found.")


def main():
    parser = argparse.ArgumentParser(description="Task manager")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add")
    p_add.add_argument("title")

    p_list = sub.add_parser("list")

    p_complete = sub.add_parser("complete")
    p_complete.add_argument("id", type=int)

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("id", type=int)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return

    {"add": cmd_add, "list": cmd_list, "complete": cmd_complete, "delete": cmd_delete}[
        args.command
    ](args)


if __name__ == "__main__":
    main()
