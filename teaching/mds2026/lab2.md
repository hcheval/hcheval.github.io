# Lab 2

## Ollama

Ollama este un serviciu care permite rularea de LLM-uri local.
Urmați [instrucțiunile oficiale](https://ollama.com/download) pentru instalare. Pe Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verificați că funcționează:

```bash
ollama --version
```

### Descărcarea și rularea unui model

```bash
ollama pull tinyllama   # descarcă modelul (~600 MB, o singură dată)
ollama run tinyllama    # pornește o sesiune interactivă
```
Veți vedea un prompt în care puteți scrie orice. Tastați `/bye` pentru a ieși.
Vedeti [https://huggingface.co/models](https://huggingface.co/models) pentru 
mai multe modele (in principiu, modele cu dimensiuni de cativa `B` ar trebui sa functioneze pe majoritatea laptop-urilor).
Incercati mai multe modele si observati diferentele dintre ele.

### Apelarea din Python

Ollama expune un API compatibil cu cel al OpenAI (un standard de facto pentru aceste aplicatii). 
Puteți folosi biblioteca oficială `openai`, schimbând doar URL-ul de bază:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # necesar de bibliotecă, dar ignorat de Ollama
)

response = client.chat.completions.create(
    model="tinyllama",
    messages=[
        {"role": "user", "content": "What is heavier between a kilogram of lead or a kilogram of feathers?"}
    ],
)
print(response.choices[0].message.content)
```

```bash
pip install openai
python client.py
```

Ca exercitiu, implementati folosind biblioteca openai, un chat similar cu cel din linia de comanda din `ollama`. 
Aspectul de care trebuie sa tineti cont este memorarea istoricului conversatiei (si transmiterea acestuia catre model).


---

## Docker

Docker este un sistem prin care putem crea un mediu izolat si replicabil de executie. 

Pentru un scurt exemplu, presupunem ca aplicația noastră are nevoie de o bază de date. Putem instala PostgreSQL local, crea un utilizator, configura totul, verifica că portul nu e ocupat, asigura că pornește la boot... sau:

```bash
docker run -e POSTGRES_PASSWORD=secret -p 5432:5432 postgres
```

Obtinand un server PostgreSQL izolat, reproductibil.
Docker împachetează o aplicație împreună cu întregul său mediu de execuție: biblioteci de sistem, runtime, dependențe, configurație, într-o imagine. O imagine rulează ca un *container*: un proces izolat care se comportă identic pe orice mașină cu Docker instalat.

---

## Notiuni de baza


|  |  |
|---|---|
| **Image** | Un snapshot read-only: aplicația + mediul ei. |
| **Container** | O instanță care rulează a unei imagini. |
| **Dockerfile** | O rețetă pentru construirea unei imagini. |
| **Registry** | Un server care stochează imagini. Docker Hub este cel public implicit. |

---

## Instalare Docker

Instalați Docker urmând [instrucțiunile oficiale](https://docs.docker.com/engine/install/). 
Activati serviciul si verificati ca functioneaza: 

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker $USER  # ca să nu fie nevoie de sudo la fiecare comandă
# delogați-vă și relogați-vă pentru ca schimbarea grupului să aibă efect
```

Verificați că funcționează:

```bash
docker run hello-world
```

Ar trebui să vedeți un mesaj care explică că Docker a descărcat imaginea `hello-world` și l-a rulat.

---

Nu trebuie întotdeauna să vă construiți propria imagine. Docker Hub are imagini pentru aproape orice infrastructură comună.

```bash
# Rulați un shell Ubuntu de unică folosință
docker run -it ubuntu bash

# În interiorul containerului avem un sistem Ubuntu complet, izolat
cat /etc/os-release
exit

# Rulați PostgreSQL (un server de baze de date)
# -d înseamnă "detached" (rulează în fundal)
# -p 5432:5432 mapează portul 5432 al mașinii host la portul 5432 al containerului
# --name dă un nume containerului
docker run --name mydb -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres

# Vedeți containerele care rulează — e acolo, rulând în tăcere
docker ps

# Deschideți un shell interactiv în container și conectați-vă la baza de date
docker exec -it mydb psql -U postgres

# Acum sunteți în interiorul bazei de date. Încercați:
#   CREATE TABLE test (id int, name text);
#   INSERT INTO test VALUES (1, 'hello');
#   SELECT * FROM test;
#   \q    (pentru a ieși)

# Opriți-l
docker stop mydb

# Ștergeți-l (containerele nu se șterg singure)
docker rm mydb
```

**Idee cheie:** flag-ul `-p host:container` este modul în care expuneți porturile containerului. Fără el, serviciul rulează dar este complet inaccesibil din afara containerului. Flag-ul `-d` rulează containerul în fundal: `docker ps` și `docker logs mydb` sunt modul în care îl monitorizați.

### Comenzi utile

```bash
docker ps              # containere care rulează
docker ps -a           # toate containerele (inclusiv cele oprite)
docker images          # imaginile de pe mașina voastră
docker rm <name>       # șterge un container
docker rmi <image>     # șterge o imagine
docker logs <name>     # stdout-ul unui container
docker exec -it <name> bash   # deschide un shell în interiorul unui container care rulează
```

---

## Configurarea unei imagini 

Crearea unei imagini se realizeaza prin specificarea unui fisier `Dockerfile`. 
Luați scriptul `main.py` din Lab 1, scriptul vostru meteo care folosește `requests`. Să îl containerizăm.
Mergeți în proiectul din Lab 1 (sau creati unul nou).

```bash
cd path/to/repo-lab1
ls
# ar trebui să vedeți main.py și requirements.txt
```

Creați un fișier numit `Dockerfile` în același director, lângă `main.py`:

```
repo-lab1/
├── main.py
├── requirements.txt
└── Dockerfile        
```

Conținutul `Dockerfile`-ului:

```dockerfile
# Pornim de la o imagine oficiala Python
FROM python:3.12-slim

# Setăm un director de lucru în interiorul containerului
WORKDIR /app

# Copiem mai întâi specificația dependențelor (pentru layer caching — explicat mai jos)
COPY requirements.txt .

# Instalăm dependențele
RUN pip install -r requirements.txt

# Copiem restul codului sursă
COPY . .

# Comanda implicită când containerul pornește
CMD ["python", "main.py"]
```

Build și rulare (`.` de la final înseamnă „folosește directorul curent ca context"):

```bash
docker build -t weather .
docker run weather
```

Ar trebui să vedeți același output ca la `python main.py` direct, dar acum va produce același output pe orice mașină cu Docker, indiferent ce versiune de Python este instalată local.

### Layer caching

Docker construiește imaginile în straturi (*layers*), câte unul per instrucțiune. Dacă un layer nu s-a schimbat față de ultimul build, Docker îl reutilizează din cache. De aceea `COPY requirements.txt` vine *înaintea* lui `COPY . .`:

- Dacă modificați doar `main.py`, Docker reutilizează layer-ul de pip install din cache.
- Dacă modificați `requirements.txt`, Docker rulează din nou pip install.

Inversarea ordinii ar cauza rularea pip install la fiecare modificare de cod.

---

### Sandboxing pentru un coding agent

Pe langa utilizarile care tin de infrastructura aplicatiei, pentru laborator ne intereseaza si izolarea agentilor AI pentru a mitiga riscurile de securitate care vin odata cu acestia.

În Laboratorul 1 am introdus opencode, si l-ați rulat direct pe mașina voastră. 
Laboratorul includea acest avertisment:

> *Agentul poate executa comenzi arbitrare pe mașina voastră, acesta este un risc important de securitate.*

Un container oferă o barieră mai dură: agentul rulează în interiorul unui container si poate vedea doar fișierele pe care le montați explicit în el. Dacă rulează `rm -rf /`, distruge filesystem-ul containerului, nu pe cel local.

### Setup

Creați un `Dockerfile` pentru opencode:

```dockerfile
FROM node:22-slim
RUN npm install -g opencode-ai@latest
WORKDIR /workspace
ENTRYPOINT ["opencode"]
```

Build:

```bash
docker build -t opencode-sandbox .
```

### Rularea agentului pe un proiect

Montați directorul proiectului în container și transmiteți cheia voastră de API (sau ignorati daca folositi doar modelele free din opencode):

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -e OPENROUTER_API_KEY=cheia_voastra_aici \
  opencode-sandbox
```

- `-v $(pwd):/workspace`: containerul vede directorul vostru curent la `/workspace`. Agentul poate citi și scrie fișiere acolo, dar nicăieri altundeva pe mașina voastră.
- `-e OPENROUTER_API_KEY=...`: agentul are nevoie de acces la rețea pentru a apela API-ul LLM; asta e în regulă. Ce nu poate face este să acceseze `~/.ssh`, `~/.aws` sau orice altă cale de pe host pe care nu ați montat-o.
- `--rm`: șterge containerul automat când ieșiți, fără nicio curățare manuală.

Daca aveti curaj si incredere ca totul a fost configurat bine, puteti cere agentului de coding sa stearga intregul fisier home,
desi sunt sanse sa refuze cererea. (dar recomandarea ar fi sa incercati asta pe o masina virtuala prima data, nu suntem responsabili pentru pierderea fisierelor).
