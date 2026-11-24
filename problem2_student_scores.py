import argparse
import sys

import matplotlib
matplotlib.use("Agg")                
import matplotlib.pyplot as plt
import pandas as pd
import requests

TIMEOUT_SECONDS = 10


def fetch_scores(url: str) -> list[dict]:
    response = requests.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    # Accept either a bare list or {"students": [...]}
    return payload["students"] if isinstance(payload, dict) else payload


def to_dataframe(records: list[dict]) -> pd.DataFrame:
    """Extract name + score, coerce scores to numbers, drop bad rows."""
    df = pd.DataFrame(records)
    missing = {"name", "score"} - set(df.columns)
    if missing:
        raise ValueError(f"API data is missing fields: {', '.join(sorted(missing))}")
    df = df[["name", "score"]].copy()
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    bad = df["score"].isna().sum()
    if bad:
        print(f"Warning: skipped {bad} record(s) with a non-numeric score.")
    return df.dropna(subset=["score"])


def plot_scores(df: pd.DataFrame, average: float, output: str) -> None:
    df = df.sort_values("score", ascending=False)
    colors = ["#2a9d8f" if s >= average else "#e76f51" for s in df["score"]]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.bar(df["name"], df["score"], color=colors, edgecolor="none", width=0.65)
    labels = ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=10)
    for label in labels:   # keep values readable where they cross the average line
        label.set_bbox(dict(facecolor="white", edgecolor="none", pad=1))

    ax.axhline(average, color="#264653", linestyle="--", linewidth=1.5)
    ax.text(len(df) - 0.5, average + 1.5, f"Average: {average:.2f}",
            ha="right", va="bottom", color="#264653", fontsize=11, fontweight="bold")

    ax.set_title("Student Test Scores", fontsize=15, fontweight="bold", pad=14)
    ax.set_xlabel("Student", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_ylim(0, 105)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    plt.xticks(rotation=30, ha="right")

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#2a9d8f", label="At or above average"),
                       Patch(color="#e76f51", label="Below average")],
              loc="upper right", bbox_to_anchor=(1, 0.93), frameon=False)

    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Student scores: average + bar chart")
    parser.add_argument("--url", help="scores API endpoint (default: bundled mock API)")
    parser.add_argument("--output", default="student_scores.png", help="chart file")
    args = parser.parse_args()

    server = None
    url = args.url
    if not url:
        from mock_scores_api import start_in_background
        server, url = start_in_background()
        print(f"Started local mock API at {url}")

    try:
        print(f"Fetching student scores from {url} ...")
        records = fetch_scores(url)
    except requests.RequestException as exc:
        sys.exit(f"API request failed: {exc}")
    finally:
        if server:
            server.shutdown()

    df = to_dataframe(records)
    if df.empty:
        sys.exit("No valid scores to process.")

    average = df["score"].mean()

    print(f"\n{'Student':<12}{'Score':>6}")
    print("-" * 18)
    for _, row in df.iterrows():
        print(f"{row['name']:<12}{row['score']:>6.0f}")
    print("-" * 18)
    print(f"Students : {len(df)}")
    print(f"Highest  : {df['score'].max():.0f} ({df.loc[df['score'].idxmax(), 'name']})")
    print(f"Lowest   : {df['score'].min():.0f} ({df.loc[df['score'].idxmin(), 'name']})")
    print(f"AVERAGE SCORE: {average:.2f}")

    plot_scores(df, average, args.output)
    print(f"\nBar chart saved to {args.output}")


if __name__ == "__main__":
    main()
