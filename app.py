import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime, timezone
from collections import defaultdict

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Repo Health Dashboard",
    page_icon="🔬",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
}

.metric-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
}

.metric-card .label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 6px;
}

.metric-card .value {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 800;
    color: #e6edf3;
}

.metric-card .sub {
    font-size: 12px;
    color: #8b949e;
    margin-top: 2px;
}

.repo-row {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}

.repo-row:hover {
    border-color: #58a6ff;
}

.repo-name {
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    font-size: 15px;
    color: #58a6ff;
}

.repo-desc {
    font-size: 13px;
    color: #8b949e;
    margin-top: 4px;
}

.tag {
    display: inline-block;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    color: #8b949e;
    margin-right: 6px;
}

.score-badge {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 22px;
    color: #3fb950;
}

stMarkdown { color: #e6edf3; }
</style>
""", unsafe_allow_html=True)


# ── GitHub API helpers ────────────────────────────────────────────────────────
GITHUB_API = "https://api.github.com"

def get_headers(token=None):
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

@st.cache_data(ttl=300)
def fetch_user(username, token=None):
    r = requests.get(f"{GITHUB_API}/users/{username}", headers=get_headers(token))
    if r.status_code == 404:
        return None, "User not found."
    if r.status_code == 403:
        return None, "Rate limit hit. Add a GitHub token for higher limits."
    r.raise_for_status()
    return r.json(), None

@st.cache_data(ttl=300)
def fetch_repos(username, token=None):
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"per_page": 100, "page": page, "type": "owner"},
            headers=get_headers(token),
        )
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

@st.cache_data(ttl=300)
def fetch_commit_activity(owner, repo, token=None):
    r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/stats/commit_activity",
        headers=get_headers(token),
    )
    if r.status_code == 200:
        return r.json()
    return []


# ── Engagement score ──────────────────────────────────────────────────────────
def engagement_score(repo):
    stars   = repo.get("stargazers_count", 0)
    forks   = repo.get("forks_count", 0)
    watches = repo.get("watchers_count", 0)
    issues  = repo.get("open_issues_count", 0)

    # Recency bonus: repos updated in last 90 days get a boost
    updated = repo.get("updated_at", "")
    recency = 0
    if updated:
        delta = (datetime.now(timezone.utc) - datetime.fromisoformat(updated.replace("Z", "+00:00"))).days
        recency = max(0, 90 - delta)

    return round(stars * 3 + forks * 2 + watches * 1 + issues * 0.5 + recency * 0.3, 1)


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("# 🔬 GitHub Repo Health Dashboard")
st.markdown("*Analyse any public GitHub profile's repo portfolio at a glance.*")
st.divider()

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    username = st.text_input("GitHub Username", placeholder="e.g. torvalds")
    token = st.text_input("GitHub Token *(optional)*", type="password",
                          help="Increases API rate limit from 60 → 5000 req/hr. Create one at github.com/settings/tokens")
    analyze_btn = st.button("Analyse →", type="primary", use_container_width=True)
    st.divider()
    st.markdown("""
**About**  
This dashboard scores every public repo by engagement (stars, forks, watchers, open issues + recency).

[View on GitHub](https://github.com) · Built with Streamlit
""")

if not username:
    st.info("👈 Enter a GitHub username in the sidebar to get started.")
    st.stop()

if analyze_btn or username:
    with st.spinner(f"Fetching data for **{username}**…"):
        user, err = fetch_user(username, token or None)
        if err:
            st.error(err)
            st.stop()

        repos = fetch_repos(username, token or None)

    if not repos:
        st.warning("This user has no public repositories.")
        st.stop()

    # ── Filter out forks ──────────────────────────────────────────────────
    original_repos = [r for r in repos if not r.get("fork")]
    forked_repos   = [r for r in repos if r.get("fork")]

    # ── Score ─────────────────────────────────────────────────────────────
    for r in original_repos:
        r["_score"] = engagement_score(r)

    original_repos.sort(key=lambda x: x["_score"], reverse=True)

    total_stars  = sum(r.get("stargazers_count", 0) for r in original_repos)
    total_forks  = sum(r.get("forks_count", 0)      for r in original_repos)
    total_issues = sum(r.get("open_issues_count", 0) for r in original_repos)

    # ── Profile header ────────────────────────────────────────────────────
    col_av, col_info = st.columns([1, 4])
    with col_av:
        st.image(user.get("avatar_url", ""), width=120)
    with col_info:
        st.markdown(f"## {user.get('name') or username}")
        st.markdown(f"`@{username}` · {user.get('bio') or ''}")
        joined = user.get("created_at", "")[:10]
        st.caption(f"📅 Joined {joined} · 👥 {user.get('followers',0):,} followers · {user.get('following',0):,} following")

    st.divider()

    # ── KPI row ───────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    kpis = [
        (k1, "Original Repos", len(original_repos), ""),
        (k2, "Total Stars",    total_stars,          "⭐"),
        (k3, "Total Forks",    total_forks,          "🍴"),
        (k4, "Open Issues",    total_issues,         "🐛"),
        (k5, "Forked Repos",   len(forked_repos),    ""),
    ]
    for col, label, val, icon in kpis:
        with col:
            st.markdown(f"""
<div class="metric-card">
  <div class="label">{label}</div>
  <div class="value">{icon}{val:,}</div>
</div>""", unsafe_allow_html=True)

    st.divider()

    # ── Charts row ────────────────────────────────────────────────────────
    chart1, chart2 = st.columns(2)

    # Language breakdown
    lang_counts = defaultdict(int)
    for r in original_repos:
        lang = r.get("language") or "Unknown"
        lang_counts[lang] += 1

    lang_df = pd.DataFrame(lang_counts.items(), columns=["Language", "Repos"]).sort_values("Repos", ascending=False)

    with chart1:
        st.markdown("### 🧑‍💻 Languages Used")
        fig = px.bar(
            lang_df.head(10), x="Repos", y="Language", orientation="h",
            color="Repos", color_continuous_scale="Blues",
            template="plotly_dark",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Stars distribution
    with chart2:
        st.markdown("### ⭐ Stars by Repo (Top 15)")
        top15 = sorted(original_repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)[:15]
        sdf = pd.DataFrame({"Repo": [r["name"] for r in top15],
                             "Stars": [r.get("stargazers_count", 0) for r in top15]})
        fig2 = px.bar(sdf, x="Stars", y="Repo", orientation="h",
                      color="Stars", color_continuous_scale="Teal",
                      template="plotly_dark")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Repo list ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🏆 Repos Ranked by Engagement Score")
    st.caption("Score = stars×3 + forks×2 + watchers + open issues×0.5 + recency bonus")

    show_forks_toggle = st.toggle("Include forked repos", value=False)
    display_repos = original_repos if not show_forks_toggle else sorted(repos, key=lambda x: x.get("_score", engagement_score(x)), reverse=True)

    for repo in display_repos[:25]:
        score = repo.get("_score", engagement_score(repo))
        lang  = repo.get("language") or "—"
        desc  = repo.get("description") or "*No description*"
        updated = repo.get("updated_at", "")[:10]
        is_fork = "🍴 Fork · " if repo.get("fork") else ""

        st.markdown(f"""
<div class="repo-row">
  <div style="display:flex; justify-content:space-between; align-items:flex-start;">
    <div>
      <div class="repo-name">📦 {repo['name']}</div>
      <div class="repo-desc">{desc}</div>
      <div style="margin-top:10px;">
        <span class="tag">{lang}</span>
        <span class="tag">⭐ {repo.get('stargazers_count',0)}</span>
        <span class="tag">🍴 {repo.get('forks_count',0)}</span>
        <span class="tag">🐛 {repo.get('open_issues_count',0)}</span>
        <span class="tag">{is_fork}Updated {updated}</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px; color:#8b949e; font-family:'DM Mono',monospace; margin-bottom:4px;">SCORE</div>
      <div class="score-badge">{score}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Commit activity for top repo ──────────────────────────────────────
    if original_repos:
        top_repo = original_repos[0]
        st.divider()
        st.markdown(f"### 📈 Commit Activity — `{top_repo['name']}` (top scored repo)")

        activity = fetch_commit_activity(username, top_repo["name"], token or None)
        if activity:
            weeks = [datetime.utcfromtimestamp(w["week"]).strftime("%b %d") for w in activity]
            totals = [w["total"] for w in activity]
            cdf = pd.DataFrame({"Week": weeks, "Commits": totals})
            fig3 = px.area(cdf, x="Week", y="Commits",
                           template="plotly_dark", color_discrete_sequence=["#58a6ff"])
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(tickangle=-45, nticks=12),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Commit activity not available for this repo (GitHub computes it asynchronously — try again in a moment).")

    st.divider()
    st.caption("Data sourced from the GitHub REST API · Cached for 5 minutes · Built with Streamlit + Plotly")
