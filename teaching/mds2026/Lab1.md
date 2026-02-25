# Sarcini de laborator

**Observatii**: 

- Este recomandat sa aveti un sistem de tip Unix pentru rezolvarea laboratoarelor 
(Linux, MacOS, sau [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install)).

- Majoritatea laboratoarelor vor fi prezentate in python, dar intentia este ca limbajul sa nu fie important. 
  Daca au sens, puteti rezolva sarcinile si in alte limbaje. 

## 1. Controlul versiunilor

Git este un sistem de **versionare a codului sursă**: ține evidența tuturor modificărilor din proiect, permite colaborarea în echipă și oferă un istoric complet al evoluției acestuia. GitHub si Gitlab sunt platforme care găzduiesc repository-uri Git și adaugă funcționalități de colaborare: pull requests, code review, issues, etc.

Dacă nu aveți deja un cont GitHub, creați unul pe [github.com](https://github.com).

**Autentificare prin SSH**

Cel mai comod mod de a lucra cu GitHub din terminal este prin SSH. Generați o pereche de chei:

```bash
ssh-keygen -t ed25519 -C "email@example.com"
```

Apăsați Enter pentru locația implicită (`~/.ssh/id_ed25519`). Copiați cheia publică:

```bash
cat ~/.ssh/id_ed25519.pub
```

Pe GitHub: **Settings → SSH and GPG keys → New SSH key**, lipiți cheia și salvați. Verificați că funcționează:

```bash
ssh -T git@github.com
```

Ar trebui să primiți: `Hi <username>! You've successfully authenticated.`

**Creați un repository**

Pe GitHub, apăsați **New repository**. Alegeți un nume, bifați **Add a README file** și creați repository-ul. Clonați-l local:

```bash
git clone git@github.com:<username>/<repo>.git
cd <repo>
```

**Fluxul de bază**

Modificați fișierul `README.md`, apoi:

```bash
git add README.md       # marcați fișierul pentru următorul commit
git commit -m "mesaj"  # creați un snapshot local
git push               # trimiteți pe GitHub
```

Pentru a prelua modificările făcute de colegi:

```bash
git pull
```

Înainte de orice sesiune de lucru, un `git pull` este o regulă bună de urmat.

## 2. Management-ul dependințelor

1. Formați echipele de proiect (2 - 3 studenți). Treceți în [tabel](https://docs.google.com/spreadsheets/d/1j7AzNxxasG1oxSRG3-GP70WWYEY997SiZWGQW5fLbPQ/edit?usp=sharing)

Scopul acestei secțiuni este să puneți un proiect Python pe GitHub astfel încât un coleg să îl poată clona și rula pe mașina sa.

**De ce virtual environments?**

Implicit, `pip install` instalează pachetele global, pe toată mașina. Dacă două proiecte au nevoie de versiuni diferite ale aceluiași pachet, pot sa apara conflicte. Virtual environments rezolvă asta: fiecare proiect are propriul mediu izolat, independent de restul sistemului.

**Creați un virtual environment în repository-ul vostru:**

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# sau
.venv\Scripts\activate      # Windows
```

Promptul se schimbă în `(.venv) $`. Orice `pip install` merge acum doar în acest mediu, nu global.

**Instalați un pachet și scrieți un script:**

```bash
pip install requests
```

Creați un fișier `main.py` care folosește pachetul instalat. Ca punct de plecare, consultați [documentația `requests`](https://requests.readthedocs.io/en/latest/) și [Open-Meteo](https://open-meteo.com/) — un API public de vreme, fără autentificare.
Acesta e doar un exemplu, puteti folosi si alte biblioteci.

**Salvați dependențele:**

```bash
pip freeze > requirements.txt
```

Deschideți `requirements.txt` — veți vedea toate pachetele instalate, cu versiunile exacte. Acesta este fișierul care permite altcuiva să recreeze mediul vostru.

**Excludeți `.venv` din git:**

Folderul `.venv` nu se commit-uiește — e mare, e specific mașinii voastre și oricum se poate recrea din `requirements.txt`. Adăugați în `.gitignore`:

```
.venv/
```

**Publicați pe GitHub:**

```bash
git add main.py requirements.txt .gitignore
git commit -m "Adaugă script și dependențe"
git push
```

**Verificați că funcționează pentru un coleg:**

Un alt membru al echipei clonează repository-ul (dacă nu l-a clonat deja) și rulează:

```bash
git pull
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Dacă scriptul rulează fără erori, înseamnă că dependințele sunt corect specificate.

## 3. Coding agents

Instalați și configurați [opencode](https://opencode.ai/).

Vom folosi ca exemplu dezvoltarea unei aplicații simple de tip TODO list din linia de comandă.
Aplicația va avea un REPL care va suporta comenzi precum crearea unei sarcini, marcarea unei sarcini drept rezolvată,
ștergerea unei sarcini, listarea tuturor sarcinilor dintr-un interval, etc.

Scopul este ca aplicația să fie implementată, cu cât mai puțină intervenție din partea voastră, de către agentul AI.

> **Warning!** Agentul poate executa comenzi arbitrare pe mașina voastră, acesta fiind, evident, un risc important de securitate.
> Vom vedea în cursuri viitoare moduri robuste de a izola un astfel de agent, dar
> pentru moment, creați un fișier `opencode.json` în rădăcina directorului proiectului, și adăugați următoarele setări:

```json
{
  "permission": {
    "bash": {
      "*": "ask",
      "python *": "allow"
    },
    "edit": { "*": "ask" },
    "webfetch": "deny",
    "external_directory": "deny"
  }
}
```

Verificați cu atenție comenzile pentru care agentul va cere voie să le execute.

Creați un fișier `SPEC.md` în care să specificați cât mai riguros aplicația care trebuie implementată
(ca punct de plecare, deja am dat mai sus o specificație incompletă și mult prea informală).
Apoi, indicați agentului să planifice și apoi să implementeze aplicația descrisă în `SPEC.md`.
Verificați dacă rezultatul corespunde specificației din `SPEC.md`,
și dacă corespunde cu ideea pe care o aveați în minte la început (cu alte cuvinte, dacă intenția din spatele aplicației este
corect capturată în `SPEC.md`)

**Notă**: Va trebui să alegeți un model. Puteți alege unul dintre modelele gratuite disponibile în opencode
(e.g., la momentul scrierii, `GLM-5`).

**Alternativ**: creați un cont pe [openrouter](https://openrouter.ai/), obțineți o cheie API și autentificați-vă în opencode cu aceasta,și alegeți în opencode un model free de la providerul OpenRouter.
Evident, puteți folosi orice alt provider dacă se întâmplă să aveți deja o cheie API (atenție la costuri)
