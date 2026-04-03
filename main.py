import json
import argparse
import subprocess
from datetime import datetime

TASK_FILE = "tasks.json"


def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(task_text):
    tasks = load_tasks()
    task = {
        "id": max([t["id"] for t in tasks], default=0) + 1,
        "task": task_text,
        "status": "pending",
        "commands": [],
        "last_step": 0,
        "created_at": str(datetime.now())
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"✅ Task added: {task_text}")


def list_tasks():
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    for t in tasks:
        print(f"[{t['id']}] {t['task']} - {t['status']} ({len(t['commands'])} cmds)")


def mark_done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            save_tasks(tasks)
            print(f"✅ Task {task_id} marked as done")
            return
    print("❌ Task not found")


def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    print(f"🗑️ Task {task_id} deleted")


def log_action(action):
    with open("logs.txt", "a") as f:
        f.write(f"{datetime.now()} - {action}\n")


def run_command(command):
    print(f"⚙️ Running: {command}")
    log_action(f"RUN: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True
        )

        print(result.stdout)
        if result.stderr:
            print("⚠️ Error:", result.stderr)

        log_action(f"OUTPUT:\n{result.stdout}")

        return result.returncode == 0  # ✅ key change

    except Exception as e:
        print("❌ Failed:", str(e))
        log_action(f"ERROR: {str(e)}")
        return False


def show_logs():
    try:
        with open("logs.txt", "r") as f:
            print(f.read())
    except:
        print("No logs yet.")


def add_command(task_id, command):
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            t["commands"].append(command)
            save_tasks(tasks)
            print(f"✅ Command added to task {task_id}")
            return

    print("❌ Task not found")


def execute_task(task_id):
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            print(f"🚀 Executing Task: {t['task']}")
            log_action(f"EXECUTE TASK {task_id}")

            for i, cmd in enumerate(t["commands"], start=1):

                if i <= t.get("last_step", 0):
                    continue

                print(f"➡️ Step {i}: {cmd}")

                success = run_command(cmd)

                if success:
                    t["last_step"] = i
                    save_tasks(tasks)
                else:
                    print(f"❌ Step {i} failed. Stopping execution.")
                    log_action(f"FAILED at step {i}: {cmd}")

                    t["status"] = "failed"
                    save_tasks(tasks)
                    return

            t["status"] = "done"
            save_tasks(tasks)
            print("✅ Task completed successfully")
            return

    print("❌ Task not found")


def retry_task(task_id):
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            if t["status"] != "failed":
                print("⚠️ Task is not in failed state")
                return

            print(f"🔁 Retrying Task: {t['task']}")
            t["status"] = "pending"
            t["last_step"] = 0
            save_tasks(tasks)

            execute_task(task_id)
            return

    print("❌ Task not found")


def resume_task(task_id):
    tasks = load_tasks()

    for t in tasks:
        if t["id"] == task_id:
            print(f"▶️ Resuming Task: {t['task']}")
            execute_task(task_id)
            return

    print("❌ Task not found")


def create_template(name):
    if name == "node":
        add_task("Node project setup")
        tasks = load_tasks()
        task_id = tasks[-1]["id"]

        add_command(task_id, "npm init -y")
        add_command(task_id, "npm install")

    elif name == "python":
        add_task("Python project setup")
        tasks = load_tasks()
        task_id = tasks[-1]["id"]

        add_command(task_id, "python -m venv venv")
        add_command(task_id, "pip install -r requirements.txt")

    else:
        print("❌ Unknown template")


def main():
    parser = argparse.ArgumentParser(description="Task Agent CLI")

    subparsers = parser.add_subparsers(dest="command")

    # add
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("task")

    # list
    subparsers.add_parser("list")

    # done
    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    # delete
    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    # run
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("command")

    # logs
    subparsers.add_parser("logs")

    # add command
    cmd_parser = subparsers.add_parser("addcmd")
    cmd_parser.add_argument("id", type=int)
    cmd_parser.add_argument("command", nargs="+")

    # execute task
    exec_parser = subparsers.add_parser("execute")
    exec_parser.add_argument("id", type=int)

    # retry
    retry_parser = subparsers.add_parser("retry")
    retry_parser.add_argument("id", type=int)

    # resume
    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("id", type=int)

    # template
    template_parser = subparsers.add_parser("template")
    template_parser.add_argument("name")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.task)
    elif args.command == "list":
        list_tasks()
    elif args.command == "done":
        mark_done(args.id)
    elif args.command == "delete":
        delete_task(args.id)
    elif args.command == "run":
        run_command(args.command)
    elif args.command == "logs":
        show_logs()
    elif args.command == "addcmd":
        add_command(args.id, " ".join(args.command))
    elif args.command == "execute":
        execute_task(args.id)
    elif args.command == "retry":
        retry_task(args.id)
    elif args.command == "resume":
        resume_task(args.id)
    elif args.command == "template":
        create_template(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()