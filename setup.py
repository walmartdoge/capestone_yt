#!/usr/bin/env python3
import getpass
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CLICKHOUSE_HOST = "clickhouse.pochop.it"
CLICKHOUSE_URL = f"https://{CLICKHOUSE_HOST}"
PROJECT_ROOT = Path(__file__).resolve().parent
IS_WINDOWS = platform.system().lower() == "windows"


def get_dbt_yml_path() -> Path:
    if (PROJECT_ROOT / "dbt_project" / "dbt_project.yml").exists():
        return PROJECT_ROOT / "dbt_project" / "dbt_project.yml"
    return PROJECT_ROOT / "dbt_project.yml"


def get_project_name() -> str:
    dbt_yml = get_dbt_yml_path()
    if dbt_yml.exists():
        content = dbt_yml.read_text(encoding="utf-8")
        m = re.search(r"^\s*name:\s*['\"]?([a-zA-Z0-9_]+)['\"]?", content, re.MULTILINE)
        if m:
            return m.group(1)
    return "yt"


def set_project_name(new_name: str) -> None:
    dbt_yml = get_dbt_yml_path()
    if not dbt_yml.exists():
        return
    old_name = get_project_name()
    content = dbt_yml.read_text(encoding="utf-8")
    content = re.sub(
        r"^(\s*name:\s*)['\"]?[a-zA-Z0-9_]+['\"]?",
        rf"\g<1>'{new_name}'",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"^(\s*project_name:\s*)['\"]?[a-zA-Z0-9_]+['\"]?",
        rf"\g<1>'{new_name}'",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        rf"^(\s{{2}}){re.escape(old_name)}:\s*$",
        rf"\g<1>{new_name}:",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    dbt_yml.write_text(content, encoding="utf-8")


def update_vscode_python_path(python_path: str) -> None:
    settings_path = PROJECT_ROOT / ".vscode" / "settings.json"
    if not settings_path.exists():
        return
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        data["python.defaultInterpreterPath"] = python_path
        data["dbt.dbtPythonPathOverride"] = python_path
        data["dbt.enableNewLineagePanel"] = True
        settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        pass


def load_existing_credentials() -> tuple[str, str]:
    profile_path = Path.home() / ".dbt" / "profiles.yml"
    if not profile_path.exists():
        return "", ""
    content = profile_path.read_text(encoding="utf-8")
    user_m = re.search(r"^\s*user:\s*([^\s#]+)", content, re.MULTILINE)
    pass_m = re.search(r'^\s*password:\s*"(.*)"', content, re.MULTILINE)
    if user_m and pass_m:
        user = user_m.group(1).strip()
        password = pass_m.group(1).replace('\\"', '"')
        return user, password
    return "", ""


def ch_query(user: str, password: str, query: str, method: str = "GET") -> str:
    headers = {
        "X-ClickHouse-User": user,
        "X-ClickHouse-Key": password,
    }
    if method == "GET":
        url = f"{CLICKHOUSE_URL}/?query={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers=headers, method="GET")
    else:
        req = urllib.request.Request(
            CLICKHOUSE_URL,
            data=query.encode("utf-8"),
            headers=headers,
            method="POST",
        )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8").strip()


def main():
    print("\n======================================================================")
    print(f"  Nastavení dbt Core + ClickHouse ({CLICKHOUSE_HOST})")
    print("======================================================================\n")

    # 1. Přihlášení a ověření účtu
    print(f"[1/5] Ověření účtu proti serveru {CLICKHOUSE_URL}...")
    ch_user, ch_pass = load_existing_credentials()
    authenticated = False

    if ch_user and ch_pass:
        try:
            ver = ch_query(ch_user, ch_pass, "SELECT version()", method="GET")
            change_user = input(
                f"  Nalezen platný profil pro účet '{ch_user}' (ClickHouse {ver}) [Enter = použít, nebo zadejte jiný login]: "
            ).strip()
            if not change_user or change_user == ch_user:
                authenticated = True
            else:
                ch_user = change_user
                ch_pass = getpass.getpass("  Zadejte své ClickHouse heslo (při psaní skryté): ")
                ver = ch_query(ch_user, ch_pass, "SELECT version()", method="GET")
                print(f"  OK: Přihlášení úspěšné (ClickHouse {ver})")
                authenticated = True
        except Exception:
            print("  Přihlášení neproběhlo, zadejte údaje znovu.")

    while not authenticated:
        try:
            ch_user = input("  Zadejte svůj ClickHouse login (username): ").strip()
        except EOFError:
            sys.exit(1)
        if not ch_user:
            print("  CHYBA: Login nesmí být prázdný.")
            continue

        ch_pass = getpass.getpass("  Zadejte své ClickHouse heslo (při psaní skryté): ")
        try:
            ver = ch_query(ch_user, ch_pass, "SELECT version()", method="GET")
            print(f"  OK: Přihlášení úspěšné (ClickHouse {ver})")
            authenticated = True
        except Exception as e:
            print(f"  CHYBA: Přihlášení selhalo ({e}). Zkuste to znovu.\n")

    # 2. Volba projektu / jmenného prostoru (yt, gt, capstone...)
    current_project = get_project_name()
    print("\n[2/5] Nastavení projektu a jmenných prostorů...")
    while True:
        try:
            entered = input(
                f"  Zadejte zkratku projektu (např. yt, gt, capstone) [Enter = {current_project}]: "
            ).strip().lower()
        except EOFError:
            entered = ""
        project_name = entered if entered else current_project
        if re.match(r"^[a-z][a-z0-9_]*$", project_name):
            break
        print("  CHYBA: Zkratka projektu smí obsahovat pouze malá písmena, čísla a podtržítko.")

    if project_name != current_project:
        set_project_name(project_name)
        print(f"  OK: Projekt v dbt_project.yml přepnut na '{project_name}'.")

    student_staging = f"{ch_user}_{project_name}_staging"
    student_marts = f"{ch_user}_{project_name}_marts"
    student_raw_db = f"{ch_user}_{project_name}_raw"

    try:
        ch_query(ch_user, ch_pass, f"CREATE DATABASE IF NOT EXISTS {student_staging}", method="POST")
        ch_query(ch_user, ch_pass, f"CREATE DATABASE IF NOT EXISTS {student_marts}", method="POST")
        print(f"  OK: Cílová schémata '{student_staging}' a '{student_marts}' jsou připravena.")
        raw_exists = ch_query(ch_user, ch_pass, f"EXISTS DATABASE {student_raw_db}", method="GET")
        if raw_exists == "1":
            print(f"  OK: Zdrojová databáze '{student_raw_db}' nalezena.")
        else:
            print(f"  UPOZORNĚNÍ: Zdrojová databáze '{student_raw_db}' zatím na serveru neexistuje.")
    except Exception as e:
        print(f"  Upozornění při kontrole schématu: {e}")

    # 3. Uložení ~/.dbt/profiles.yml
    dbt_dir = Path.home() / ".dbt"
    dbt_dir.mkdir(parents=True, exist_ok=True)
    profile_path = dbt_dir / "profiles.yml"
    print(f"\n[3/5] Ukládání profilu do {profile_path}...")

    escaped_pass = ch_pass.replace('"', '\\"')
    profile_content = f"""dbs_project:
  target: dev
  outputs:
    dev:
      type: clickhouse
      driver: http
      host: {CLICKHOUSE_HOST}
      port: 443
      user: {ch_user}
      password: "{escaped_pass}"
      schema: {student_staging}
      secure: true
      verify: true
      connect_timeout: 15
      send_receive_timeout: 300
"""
    profile_path.write_text(profile_content, encoding="utf-8")
    print(f"  OK: Profil uložen do {profile_path}")

    if shutil.which("git"):
        name = subprocess.run(["git", "config", "--global", "user.name"], capture_output=True, text=True).stdout.strip()
        email = subprocess.run(["git", "config", "--global", "user.email"], capture_output=True, text=True).stdout.strip()
        if not name:
            subprocess.run(["git", "config", "--global", "user.name", ch_user], check=False)
        if not email:
            subprocess.run(["git", "config", "--global", "user.email", f"{ch_user}@local"], check=False)

    # 4. Instalace dbt-clickhouse
    print("\n[4/5] Příprava Python prostředí a instalace dbt-clickhouse...")
    if not IS_WINDOWS:
        dbt_bin = shutil.which("dbt")
        if not dbt_bin:
            print("  Instaluji dbt-clickhouse (cca 20-40 s)...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "dbt-clickhouse"], check=True)
            candidate = Path(sys.executable).resolve().parent / "dbt"
            dbt_bin = shutil.which("dbt") or (str(candidate) if candidate.exists() else "dbt")
        update_vscode_python_path(sys.executable)
        print(f"  OK: dbt-clickhouse je nainstalován ({dbt_bin}).")
    else:
        venv_dir = PROJECT_ROOT / ".venv"
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_dbt = venv_dir / "Scripts" / "dbt.exe"
        if not venv_python.exists():
            print("  Vytvářím virtuální prostředí .venv...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        if not venv_dbt.exists():
            print("  Instaluji dbt-clickhouse (cca 30-60 s)...")
            subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "--quiet"], check=True)
            subprocess.run([str(venv_python), "-m", "pip", "install", "dbt-clickhouse", "--quiet"], check=True)
        dbt_bin = str(venv_dbt)
        update_vscode_python_path("${workspaceFolder}/.venv/Scripts/python.exe")
        print("  OK: dbt-clickhouse je připraven v .venv.")

    # 5. VS Code rozšíření a dbt debug
    print("\n[5/5] Kontrola rozšíření a spuštění 'dbt debug'...")
    code_cmd = shutil.which("code")
    if code_cmd:
        for ext in [
            "innoverio.vscode-dbt-power-user",
            "samuelcolvin.jinjahtml",
            "redhat.vscode-yaml",
            "cldwalker.clickhouse-language-support",
        ]:
            subprocess.run([code_cmd, "--install-extension", ext, "--force"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    dbt_work_dir = PROJECT_ROOT / "dbt_project" if (PROJECT_ROOT / "dbt_project" / "dbt_project.yml").exists() else PROJECT_ROOT
    subprocess.run([dbt_bin, "debug"], cwd=str(dbt_work_dir), check=False)

    print("\n======================================================================")
    print(f"  Hotovo. Projekt '{project_name}' je připraven ({student_raw_db} -> {student_staging} -> {student_marts}).")
    print("======================================================================")
    print("  Příkazy: dbt run | dbt test | dbt build\n")


if __name__ == "__main__":
    main()
