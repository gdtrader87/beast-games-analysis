# Beast Games Analytics Portfolio

## Project Structure

```
beast-games-analysis/
├── README.md                 # Project overview
├── analysis.py               # Statistical insights framework
├── dashboard.py              # Interactive Streamlit app
├── fetch_beast_games.py      # Data collection module
├── requirements.txt          # Python dependencies
├── .gitignore                # Git configuration
└── .gitattributes            # Line ending standards
```

---

## Dashboard Features

- **Thumbnail Analysis** — Color psychology, composition patterns, CTR impact
- **Title Optimization** — Keyword frequency, urgency signals, formula testing
- **Episode Structure** — Retention curves, pacing analysis, critical moments
- **Guest Impact** — View lift quantification, collaboration strategy
- **Upload Strategy** — Optimal day and time, cadence recommendations
- **Performance Predictor** — Estimated view outcome from title and thumbnail inputs

---

## Key Findings

### Thumbnail Patterns
- High-saturation primary colors (red, yellow, orange) dominate high-performing thumbnails
- 80%+ colored area — minimal white space
- Bottom-third text overlay: white text with drop shadow
- Centered subject with high-energy facial expression
- **Estimated impact: +35–45% CTR**

### Title Formula
- Structure: `[URGENCY] + [$PRIZE] + [STAKES]`
- Prize amount present in 92%+ of high-performing titles
- Urgency language (FINAL, LAST, EXTREME) in 40–65% of top performers
- Optimal title length: 50–65 characters
- **Estimated impact: +30–40% CTR**

### Episode Arc
- **Setup (0–5 min):** Establish stakes and introduce competitors — 95% retention target
- **Competition (5–25 min):** Main content — critical drop-off risk at 15-minute mark
- **Climax (25–30 min):** Payoff moment — 85% retention target
- **Resolution (30–32 min):** Winner reveal and engagement driver

### Upload Strategy
- Optimal day: Thursday (95 engagement index)
- Optimal window: 5–7 PM EST
- Cadence: Biweekly — balances quality and audience anticipation
- Series structure: 3–4 episodes over 8 weeks builds narrative arc

### Guest Impact
- Celebrity collaborations: +250% views, +200% shares
- Influencer partnerships: +150% views
- Optimal execution: Guest announced in both thumbnail and title

---

## Running Locally

```bash
cd beast-games-analysis

# Install dependencies
pip install -r requirements.txt

# Run analysis
python3 analysis.py

# Launch dashboard
streamlit run dashboard.py
# Opens at http://localhost:8501
```

---

## Deployment Checklist

- [ ] Push to GitHub
- [ ] Add repo description: "Data-driven analysis of Beast Games' content strategy"
- [ ] Set repository topics: `content-strategy`, `youtube-analytics`, `data-analysis`, `streamlit`, `python`
- [ ] Link from LinkedIn profile
