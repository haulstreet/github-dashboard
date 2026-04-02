# 🔬 GitHub Repo Health Dashboard

Check it out here! -> https://apppydashboard.streamlit.app/

A Streamlit web app that analyses any public GitHub profile and scores every repository by engagement — giving you an instant, data-driven view of a developer's portfolio.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

| Feature | Details |
|---|---|
| 👤 Profile overview | Avatar, bio, follower count, join date |
| 📊 KPI cards | Total stars, forks, open issues, repo counts |
| 🧑‍💻 Language chart | Bar chart of top languages across all repos |
| ⭐ Stars chart | Top 15 repos by star count |
| 🏆 Engagement score | Custom formula ranks every repo by health |
| 📈 Commit activity | 52-week area chart for the top-scored repo |
| 🍴 Fork toggle | Show/hide forked repos from rankings |
| 🔑 Token support | Optional GitHub PAT for 5,000 req/hr rate limit |

### Engagement Score Formula

```
Score = (stars × 3) + (forks × 2) + watchers + (open issues × 0.5) + recency bonus
```

Repos updated within the last 90 days receive a bonus proportional to how recently they were active — rewarding maintained projects.

---

## 🚀 Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/github-dashboard.git
cd github-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

---

---

## 🔑 GitHub Token (Optional but Recommended)

Without a token, the GitHub API allows **60 requests/hour**.  
With a token, this increases to **5,000 requests/hour**.

To generate a token:
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Select **no scopes** (read-only public data needs none)
4. Copy the token and paste it into the sidebar field in the app

> ⚠️ Never commit your token to the repo. The sidebar input is `type="password"` so it's masked on screen.

---

## 🗂️ Project Structure

```
github-dashboard/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🛠️ Tech Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Plotly](https://plotly.com/python/)** — Interactive charts
- **[Pandas](https://pandas.pydata.org)** — Data manipulation
- **[GitHub REST API](https://docs.github.com/en/rest)** — Data source

---

## 📄 License

MIT — free to use, modify, and distribute.
