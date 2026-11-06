# dbt + ClickHouse – Starter projekt

## 1. Vytvoření vlastního repozitáře ze šablony

1. Klikněte na GitHubu nahoře na tlačítko **Use this template → Create a new repository**.
2. Zvolte název repozitáře a klikněte na **Create repository**.

---

## 2. Otevření projektu

### Možnost A: Lokálně ve Visual Studio Code
1. Otevřete **Visual Studio Code** na svém počítači.
2. Stiskněte `Ctrl + Shift + P`, napište **`Git: Clone`** a vyberte **`Clone from GitHub`**.
3. Vyberte svůj nově vytvořený repozitář, uložte ho na disk a klikněte na **Open**.

### Možnost B: GitHub Codespaces
1. Na stránce svého repozitáře na GitHubu klikněte na zelené tlačítko **`<> Code`**.
2. Přepněte na záložku **Codespaces** a klikněte na **Create codespace on main**.

---

## 3. Nastavení připojení a volba projektu

Otevřete terminál ve VS Code (`Ctrl + ~`) a spusťte:

```bash
python setup.py
```

Skript:
1. Ověří váš ClickHouse login a heslo (při opakovaném spuštění použije již uložený profil z `~/.dbt/profiles.yml`).
2. Zeptá se na zkratku projektu (`yt`, `gt`, `capstone` apod.), nastaví ji v `dbt_project.yml` a připraví v ClickHouse schémata `<login>_<projekt>_staging` a `<login>_<projekt>_marts` (zdrojová data se čtou z `<login>_<projekt>_raw`).
3. Nainstaluje `dbt-clickhouse` a ověří spojení příkazem `dbt debug`.

---

## 4. Základní příkazy

```bash
dbt debug                        # Ověření připojení k ClickHouse
dbt compile                      # Překlad Jinja šablon do čistého SQL (složka target/compiled)
dbt run                          # Spuštění všech modelů
dbt run -s nazev_modelu          # Spuštění jednoho konkrétního modelu
dbt test                         # Spuštění testů kvality dat
dbt build                        # Spuštění modelů i testů najednou
```

Příkazy můžete spouštět také přes menu úloh ve VS Code klávesovou zkratkou **`Ctrl + Shift + B`** nebo tlačítky nad SQL kódem.
