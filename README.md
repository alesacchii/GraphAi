# AgenticAI

Esempio didattico di come costruire un **flusso agentico** con [LangGraph](https://langchain-ai.github.io/langgraph/) e un LLM multimodale tramite [OpenRouter](https://openrouter.ai/).

Il progetto mostra come usare LangGraph per orchestrare più step di elaborazione (nodi) connessi da archi condizionali, applicandolo a un caso concreto: **estrarre dati strutturati da email di voli aerei**.

> ⚠️ Il dominio (email di compagnie aeree) è solo un pretesto per illustrare i concetti di LangGraph: stato condiviso, nodi, archi condizionali, structured output. In un progetto reale i prompt e i nodi vanno adattati al proprio dominio.

---

## Cosa fa il progetto

A partire da un file `.eml`, la pipeline:

1. **Converte la mail in immagine** (PNG) preservando la formattazione originale.
2. **Classifica** la mail in una di queste categorie:
   - `Confirmation` — conferma di prenotazione
   - `Cancellation` — cancellazione di un volo
   - `Schedule Change` — cambio di orario/data
   - `Not Useful` — newsletter, spam, irrilevante
3. **Estrae i dati strutturati** (PNR + lista voli con airport, date, orari, passeggeri) tramite un LLM multimodale che "legge" l'immagine.
4. **Valida** i dati estratti confrontandoli con l'immagine originale: se la validazione fallisce, il grafo torna indietro al nodo di classificazione per riprovare (loop di self-correction).
5. Se la mail è classificata `Not Useful`, il grafo termina senza fare estrazione.

L'output finale è un dizionario tipato (`EmailState`) con:

```python
{
    "document_category": "Confirmation",
    "pnr": "6A5T4Q",
    "flights": [FlightData, ...],
    "validator_check": True
}
```

---

## Il grafo LangGraph

Il cuore didattico del progetto è il grafo definito in [src/graph_config/graph.py](src/graph_config/graph.py):

```
       START
         │
         ▼
   email_to_image       (nodo: .eml → PNG)
         │
         ▼
     categorize  ◄──────────────────┐
         │                          │
   ┌─────┴────────────────┐         │
   │ Confirmation /       │ Not Useful
   │ Cancellation /       ▼         │
   │ Schedule Change     END        │
   ▼                                │
 extractor               (nodo: LLM estrae PNR + voli)
   │                                │
   ▼                                │
 validator               (nodo: LLM verifica i dati estratti)
   │                                │
   ├── validator_check == False ────┘  (loop: torna a categorize)
   │
   └── validator_check == True
         │
         ▼
        END
```

Concetti LangGraph illustrati:

- **`StateGraph(EmailState)`** — il grafo è tipizzato sullo stato condiviso ([src/graph_config/state.py](src/graph_config/state.py)).
- **`add_node(name, fn)`** — ogni nodo è una funzione `state -> dict` che aggiorna lo stato.
- **`add_edge(a, b)`** — transizione lineare.
- **`add_conditional_edges`** — il routing dipende dall'output di una funzione: prima sul `document_category` (extractor vs END), poi sul `validator_check` (END vs loop su `categorize`).
- **Cicli nel grafo** — il ritorno da `validator` a `categorize` mostra come LangGraph gestisce loop di self-correction in modo nativo.
- **`graph.compile()`** + **`draw_mermaid_png()`** — compilazione e diagramma del grafo (`graph.png`).

---

## Struttura del progetto

```
AgenticAI/
├── main.py                          # Entry point: costruisce il grafo e lo invoca su un .eml
├── graph.png                        # Diagramma del grafo generato a runtime
├── pyproject.toml                   # Dipendenze e metadati progetto (uv)
├── uv.lock                          # Lockfile riproducibile generato da uv
├── .env                             # Variabili d'ambiente (non versionato)
└── src/
    ├── log_config/                  # Logger colorato condiviso (singleton)
    │   ├── __init__.py
    │   └── logger.py
    ├── graph_config/
    │   ├── graph.py                 # Definizione del grafo (nodi + archi)
    │   └── state.py                 # EmailState e FlightData (TypedDict)
    ├── graph_node/
    │   ├── email_to_image.py        # Nodo: .eml → PNG
    │   ├── categorize.py            # Nodo: classificazione via LLM
    │   ├── extractor.py             # Nodo: estrazione strutturata via LLM
    │   └── validator.py             # Nodo: validazione dati estratti vs immagine
    ├── model_config/
    │   └── model.py                 # AgentConfig: wrapper LLM con structured output + retry
    ├── util/
    │   ├── prompt.py                # Prompt di classificazione ed estrazione
    │   ├── schema.py                # Pydantic schema per structured output
    │   └── base64.py                # Helper per encoding immagini
    └── data/
        ├── email/                   # File .eml di esempio
        └── email_img/               # Immagini PNG generate
```

---

## Componenti principali

### 1. Lo stato — [src/graph_config/state.py](src/graph_config/state.py)
`EmailState` è un `TypedDict` che descrive l'unico oggetto che attraversa tutto il grafo. Ogni nodo legge i campi che gli servono e ne aggiorna alcuni; LangGraph fa il merge automaticamente. I campi principali sono `file_path`, `image_path`, `document_category`, `pnr`, `flights` e `validator_check`.

### 2. I nodi — [src/graph_node/](src/graph_node/)
Ogni nodo è una funzione pura `state -> dict`:
- **`email_to_image`** — legge l'`.eml`, estrae l'HTML (o un fallback testuale) e lo screenshotta in PNG con `html2image`.
- **`categorize`** — invia l'immagine al modello con il `category_prompt` e ottiene una `DocumentClassificationSchema`.
- **`extractor`** — sceglie il prompt giusto in base alla categoria ed estrae PNR + lista voli in formato `ExtractorSchema`.
- **`validator`** — invia al modello sia i dati estratti (come JSON) sia l'immagine originale e chiede una verifica di coerenza, restituendo un `ValidatorSchema` con il flag booleano `validator_check`. Se `False`, il grafo torna su `categorize` per ritentare l'intero flusso.

### 3. `AgentConfig` — [src/model_config/model.py](src/model_config/model.py)
Wrapper sopra `init_chat_model`. Gestisce:
- la creazione del chat model (provider OpenRouter),
- l'invocazione con **structured output** (`with_structured_output(schema, method="json_schema")`),
- un meccanismo di **retry automatico** se l'output non rispetta lo schema Pydantic.

### 4. Logger — [src/log_config/logger.py](src/log_config/logger.py)
Logger colorato condiviso (basato su `colorlog`), istanziato una sola volta. Tutti i moduli lo importano con:
```python
from src.log_config import logger
```
e logga le entrate/uscite di ogni nodo del grafo (`[NODE: ...]`) per rendere visibile il flusso di esecuzione.

---

## Flusso di esecuzione

1. `main.py` importa il logger (così viene inizializzato una sola volta) e costruisce il grafo.
2. Il grafo viene invocato con `graph.invoke({"file_path": "..."})`.
3. LangGraph esegue i nodi nell'ordine definito, propagando lo stato.
4. L'arco condizionale dopo `categorize` indirizza verso `extractor` o verso `END` in base a `document_category`.
5. Dopo l'`extractor`, il nodo `validator` controlla la qualità dell'estrazione: se `validator_check` è `True` il grafo termina, altrimenti rientra in `categorize` per un nuovo tentativo.
6. Lo stato finale viene loggato.

---

## Setup

### Requisiti
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) come package manager
- Una API key di [OpenRouter](https://openrouter.ai/) con un modello multimodale (es. `openai/gpt-4o-mini`)
- Google Chrome installato (richiesto da `html2image` per generare gli screenshot)

### Installazione

Il progetto usa [uv](https://docs.astral.sh/uv/) per la gestione di virtual env e dipendenze. Le dipendenze sono dichiarate in `pyproject.toml` e bloccate in `uv.lock`.

```bash
# Sincronizza l'ambiente (crea .venv e installa le dipendenze dal lockfile)
uv sync
```

`uv sync` crea automaticamente un `.venv` nella root del progetto e installa esattamente le versioni indicate in `uv.lock`.

### Variabili d'ambiente

Crea un file `.env` nella root con:

```
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL_NAME=openai/gpt-4o-mini
```

### Esecuzione

```bash
uv run python main.py
```

In alternativa, dopo aver attivato il virtual env (`.venv\Scripts\activate` su Windows, `source .venv/bin/activate` su macOS/Linux) puoi lanciare direttamente `python main.py`.

### Gestione delle dipendenze

```bash
uv add <package>           # aggiunge una dipendenza a pyproject.toml e uv.lock
uv remove <package>        # rimuove una dipendenza
uv lock --upgrade          # aggiorna il lockfile alle ultime versioni compatibili
```

Modifica `main.py` per puntare al `.eml` che vuoi processare:

```python
result = graph.invoke({"file_path": "src/data/email/Confirmation.eml"})
```

A fine esecuzione viene anche generato `graph.png`, il diagramma Mermaid del grafo.

---

## Estendere il progetto

- **Nuova categoria di email**: aggiungi un valore al `Literal` di `EmailState.document_category`, una voce nella mappa di `add_conditional_edges` e (se serve) un nuovo prompt in `util/prompt.py`.
- **Nuovo nodo**: definisci una funzione `state -> dict` in `src/graph_node/`, registrala con `builder.add_node(...)` e collegala con `add_edge` o `add_conditional_edges`.
- **Nuovo schema di output**: definisci una classe Pydantic in `util/schema.py` e passala a `agent_config.invoke_structured(...)`.
