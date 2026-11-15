# 🍋 SavourAI — FREE LOCAL AI Recipe Generator with Ollama + Llama 3.2

**No Groq, no API key, no paid AI service.** SavourAI runs on your Windows PC using your already-installed `llama3.2` model through Ollama's local HTTP API.

## Features

- Same premium food-themed **Streamlit** UI: cream / forest-green / orange, recipe hero, ingredient starters.
- **Exactly 5 LangGraph nodes**: Available Ingredients → Ingredient Analyzer → Recipe Generator → Nutrition Advisor → Cooking Tips Generator.
- User enters ingredients and selects cuisine, diet, servings, cooking time, spice level, excluded ingredients.
- Generates recipe name, required ingredients with quantities, cooking steps, approximate calories and macronutrients, plus chef tips.
- Local **SQLite** history with favorites, revisit/delete, Markdown export.
- Ollama model picker, detected installed models, and a **Test local Ollama connection** button.
- Local AI generation works without internet *after you have downloaded Ollama, the model, and Python dependencies*. Decorative photography / fonts may require internet to load, but AI and recipe history do not.

## IMPORTANT: Which folder should I open?

The download is a FLAT ZIP: after extraction, **`app.py` and `requirements.txt` are in the SAME folder as `README.md`**. Open this exact extracted folder in VS Code and run your commands there. **You do not need `cd savourai_recipe_generator`** with this new ZIP.

## First-time setup — Windows / PowerShell

1. Install Ollama for Windows (already done if you use `ollama list`).
2. In a separate PowerShell terminal, verify your local model:

   ```powershell
   ollama list
   ollama run llama3.2
   ```

   If the model is installed, you should receive a response. Type `/bye` to exit chat. If Ollama is not serving requests, launch **Ollama** from the Start menu. Alternatively run `ollama serve` in a **separate** terminal (only if the Ollama app is not already running).

3. Open the folder **containing `app.py`** in VS Code, open Terminal → New Terminal. Run:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   Python 3.12 recommended. If `py -3.12` is unavailable, run `py -0p` to see installed versions. If you use another Python version, packages must support it.

4. `.env` is **optional**. Default model is `llama3.2`. To customize, copy the example:

   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   Example content:

   ```env
   OLLAMA_MODEL=llama3.2
   OLLAMA_URL=http://127.0.0.1:11434
   ```

   **No `GROQ_API_KEY` is needed.** Older `.env` values named `GROQ_API_KEY` are ignored; you may remove them.

5. Run from the folder containing `app.py`:

   ```powershell
   python -m streamlit run app.py
   ```

   Open **http://localhost:8501**. Do not use the VS Code “Run Python File” button for Streamlit.

**Easier option:** Double-click `start_windows.bat` in the extracted folder (after you have installed Ollama and downloaded `llama3.2`). It creates a Python environment if needed, installs packages, and runs Streamlit.

## Troubleshooting

| Error | Fix |
|---|---|
| `File does not exist: app.py` | Run `dir app.py`. Open the extracted folder containing `app.py` in VS Code. |
| `requirements.txt` missing | Run `dir requirements.txt`. You're in the wrong folder. |
| `No module named streamlit` | Activate `.venv` and install `python -m pip install -r requirements.txt`. |
| `Cannot reach Ollama` | Launch Ollama desktop (or, if not already running, `ollama serve` in another terminal), then refresh. |
| `llama3.2` not found | Run `ollama list`. If absent, run `ollama pull llama3.2`. Model name must match. |
| JSON generation error | Llama 3.2 is a small local model. Click Generate again, reduce ingredients or try shorter cooking preferences. The app retries one malformed JSON response automatically. |
| Slow generation | Llama 3.2 runs locally using your available CPU/GPU/RAM. Its four AI calls may take longer than Groq cloud inference, especially on CPU. |
| Port 8501 is busy | Streamlit will usually offer another port, or stop the previous app with Ctrl+C. |

## Workflow

```text
START
 ↓
1. available_ingredients        [Python: sanitize and validate ingredients]
 ↓
2. ingredient_analyzer         [Ollama llama3.2 call]
 ↓
3. recipe_generator            [Ollama llama3.2 call]
 ↓
4. nutrition_advisor           [Ollama llama3.2 call]
 ↓
5. cooking_tips_generator      [Ollama llama3.2 call]
 ↓
END → SQLite + Streamlit UI
```

There are exactly **five** real `StateGraph` nodes and four local Ollama model requests. No API key is sent anywhere.

## Project files

```text
app.py                 — food-themed Streamlit dashboard
workflow.py            — five-node LangGraph StateGraph
ollama_client.py       — Ollama REST client (uses only Python stdlib + dotenv)
storage.py             — SQLite recipe history/favorites
utils.py               — user input and Markdown export
requirements.txt       — Python packages
.env.example           — OPTIONAL model and localhost settings
.streamlit/config.toml — theme
start_windows.bat      — easy Windows startup
data/                  — SQLite database created when needed
tests/                 — offline tests
```

Run offline tests:

```powershell
python -m pip install pytest
python -m pytest -q
```

### A note on nutrition and allergies

AI-generated nutrition is **only a rough estimate**, not a verified analysis from a food database. The model can make mistakes with ingredient amounts, allergies and dietary restrictions. Check food labels yourself, especially if avoiding an allergen. Follow standard safe-food handling practices.

### Local-only AI privacy

Recipe-generation requests are sent to your local Ollama endpoint, `http://127.0.0.1:11434`. The app does not use Groq, open an API account, or transmit ingredient text to a cloud LLM. External decorative images and Google fonts may be fetched by the browser if online.
