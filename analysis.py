"""College-to-university transfers in BC.

Question: how do BC college students move into universities, and how well
do they do once there?

Source: BCCAT, "Profile and Performance of BC Transfer Students
(2018/19-2022/23)" (January 2025, Wong, Franzova & Bajracharya, Langara
College). The report publishes tables as PDF only, so the tables used
here were transcribed into data/ (see SOURCES in the README for the
table behind every file). This script analyses the transcribed tables,
prints findings, and draws the charts. It never downloads anything.

Definitions (report, Appendix A):
  * BC transfer student: a student transferring 15 or more credits from a
    BC Transfer System member institution.
  * BC direct entry student: a student who entered a receiving university
    after graduating from a BC high school.
  * Receiving institutions in this period (10): CapU, KPU, RRU, SFU, TRU,
    UFV, UBCV, UBCO, UNBC, UVic. UFV data were unavailable for the
    credit-band, average-credit, and completion tables, so those tables
    cover 9 receivers.

Run: python analysis.py  (prints findings, writes charts to charts/)
     pytest               (checks the transcription against the report's
                            own published totals)
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SCRATCH = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRATCH, "data")
CHART_DIR = os.path.join(SCRATCH, "charts")

# Report-level figures (executive summary / Section 1 text), kept as
# constants because they are not in any single transcribed table.
PUBLISHED_TOTAL_TRANSFER = 29798
PUBLISHED_TOTAL_DIRECT = 73680
PREV_TOTAL_TRANSFER = 30140  # 2024 report's comparison figure; see README
PREV_TOTAL_DIRECT = 53036
PREV_AVG_CREDITS = 48.6  # 2013/14-2017/18, via BCCAT's summary of the 2020 report
OVERALL_AVG_CREDITS = 46.4
COMPLETION_ADMITTED = 5802  # 2018/19 transfer cohort, 9 receivers (excl. UFV)
COMPLETION_GRADUATES = 4382
DIRECT_COMPLETION_ADMITTED = 11122  # 2016/17 direct-entry cohort; KPU excluded
DIRECT_COMPLETION_GRADUATES = 7566
MONTHS_FROM_60_TRANSFER = 29.6
MONTHS_FROM_60_DIRECT = 29.2
MONTHS_TOTAL_TRANSFER = 37.6
MONTHS_TOTAL_DIRECT = 53.0


def load(name):
    return pd.read_csv(os.path.join(DATA_DIR, name))


def compute_yearly(by_year):
    """Transfer totals by year plus the transfer share of each cohort."""
    out = by_year.copy()
    out["cohort"] = out["transfer"] + out["direct_entry"]
    out["transfer_share_pct"] = out["transfer"] / out["cohort"] * 100
    return out


def compute_receiver_shares(by_receiver):
    """Transfer share of each receiver's combined transfer + direct intake."""
    out = by_receiver.copy()
    out["cohort"] = out["transfer"] + out["direct_entry"]
    out["transfer_share_pct"] = out["transfer"] / out["cohort"] * 100
    return out


def summarise(yearly, by_receiver, by_region, bands, avg_credits,
              completion, senders):
    """Headline findings as plain numbers, for printing and testing."""
    total_transfer = by_receiver["transfer"].sum()
    peak_year = yearly.loc[yearly["transfer"].idxmax(), "year"]
    peak_value = yearly["transfer"].max()
    latest = yearly.iloc[-1]
    sfu = by_receiver.loc[by_receiver["receiver"] == "SFU", "transfer"].iloc[0]
    return {
        "total_transfer": total_transfer,
        "total_direct": by_receiver["direct_entry"].sum(),
        "transfer_share_overall": total_transfer / (
            total_transfer + by_receiver["direct_entry"].sum()) * 100,
        "peak_year": peak_year,
        "peak_value": peak_value,
        "latest_year": latest["year"],
        "latest_value": latest["transfer"],
        "latest_share": latest["transfer_share_pct"],
        "change_peak_to_latest": (latest["transfer"] / peak_value - 1) * 100,
        "sfu_share": sfu / total_transfer * 100,
        "mainland_share": by_region.loc[
            by_region["region"] == "Mainland/Southwest", "total"].iloc[0]
            / total_transfer * 100,
        "band_30_34_pct": bands.loc[bands["band"] == "30-34", "pct"].iloc[0],
        "band_60_64_pct": bands.loc[bands["band"] == "60-64", "pct"].iloc[0],
        "band_65plus_count": bands.loc[bands["band"] == "65+", "count"].iloc[0],
        "bands_base": bands["count"].sum(),
        "avg_credits_overall": OVERALL_AVG_CREDITS,
        "avg_credits_high": avg_credits.loc[
            avg_credits["avg_credits"].idxmax(), "receiver"],
        "avg_credits_high_value": avg_credits["avg_credits"].max(),
        "avg_credits_low": avg_credits.loc[
            avg_credits["avg_credits"].idxmin(), "receiver"],
        "avg_credits_low_value": avg_credits["avg_credits"].min(),
        "completion_rate": COMPLETION_GRADUATES / COMPLETION_ADMITTED * 100,
        "direct_completion_rate": DIRECT_COMPLETION_GRADUATES
            / DIRECT_COMPLETION_ADMITTED * 100,
        "top_sender": senders.iloc[0]["sender"],
        "top_sender_total": senders.iloc[0]["total"],
        "top_sender_receiver": senders.iloc[0]["top_receiver"],
        "top_sender_receiver_count": senders.iloc[0]["top_receiver_count"],
    }


def print_findings(f):
    """Print the headline findings."""
    print("=== FINDINGS (BCCAT transfer students, 2018/19-2022/23) ===")
    print(f"Transfer students: {f['total_transfer']:,} over 5 years; "
          f"direct entry: {f['total_direct']:,}; "
          f"transfer share of cohort: {f['transfer_share_overall']:.1f}%")
    print(f"Yearly peak: {f['peak_value']:,} in {f['peak_year']}; "
          f"latest ({f['latest_year']}): {f['latest_value']:,} "
          f"({f['change_peak_to_latest']:+.1f}% from peak, "
          f"{f['latest_share']:.1f}% of that year's cohort)")
    print(f"SFU takes {f['sfu_share']:.1f}% of all transfer students; "
          f"Mainland/Southwest sends {f['mainland_share']:.1f}%")
    print(f"Credits at admission: 30-34 credits {f['band_30_34_pct']}% of "
          f"students; 60-64 credits {f['band_60_64_pct']}%; "
          f"65+ credits: {f['band_65plus_count']:,} students "
          f"(base {f['bands_base']:,}, UFV excluded)")
    print(f"Average credits transferred: {f['avg_credits_overall']} overall; "
          f"highest {f['avg_credits_high']} ({f['avg_credits_high_value']}); "
          f"lowest {f['avg_credits_low']} ({f['avg_credits_low_value']})")
    print(f"Degree completion (2018/19 transfer cohort): "
          f"{f['completion_rate']:.1f}% vs "
          f"{f['direct_completion_rate']:.1f}% direct entry (2016/17 cohort)")
    print(f"Top sender: {f['top_sender']} ({f['top_sender_total']:,}), "
          f"of which {f['top_sender_receiver_count']:,} went to "
          f"{f['top_sender_receiver']}")


def _save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, name + ".png"), dpi=150)
    fig.savefig(os.path.join(CHART_DIR, name + ".svg"))
    plt.close(fig)


def plot_executive_summary(yearly, chart_dir):
    """One polished chart for the headline story.

    Bars: transfer students by year. Line: transfer share of that year's
    combined transfer + direct-entry cohort.
    """
    x = range(len(yearly))
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x, yearly["transfer"], color="#1F4E79", label="BC transfer students")
    ax.set_ylabel("BC transfer students admitted")
    ax.set_ylim(0, yearly["transfer"].max() * 1.15)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax2 = ax.twinx()
    ax2.plot(x, yearly["transfer_share_pct"], color="#C55A11", marker="o",
             markersize=4, linewidth=2, label="Transfer share of cohort (%)")
    ax2.set_ylabel("Transfer share of cohort (%)")
    ax2.set_ylim(0, yearly["transfer_share_pct"].max() * 1.3)
    ax2.spines["top"].set_visible(False)
    peak_idx = list(yearly["transfer"]).index(yearly["transfer"].max())
    ax.annotate(f"Peak {yearly['year'].iloc[peak_idx]}: "
                f"{yearly['transfer'].iloc[peak_idx]:,}",
                (peak_idx, yearly["transfer"].iloc[peak_idx]),
                textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
    ax.set_xticks(list(x), yearly["year"])
    ax.set_title("BC transfer students by year — and their share of the cohort",
                 fontsize=13, fontweight="bold", pad=12)
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="upper left")
    _save(fig, "executive_summary")


def plot_by_receiver(by_receiver, chart_dir):
    """Transfer students by receiving institution (5-year totals)."""
    data = by_receiver.sort_values("transfer", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(data["receiver"], data["transfer"], color="#1F4E79")
    for i, value in enumerate(data["transfer"]):
        ax.text(value + max(data["transfer"]) * 0.01, i, f"{value:,}",
                va="center", fontsize=9)
    ax.set_xlabel("BC transfer students admitted, 2018/19-2022/23")
    ax.set_title("Where transfer students go: by receiving institution")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    _save(fig, "transfer_by_receiver")


def plot_credit_bands(bands, chart_dir):
    """Distribution of credits transferred at admission.

    The two peak bands (start of second year, 30-34; start of third year,
    60-64) are highlighted; the base excludes UFV (data unavailable).
    """
    colors = ["#1F4E79" if b in ("30-34", "60-64") else "#7FB3D5"
              for b in bands["band"]]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(bands["band"], bands["pct"], color=colors)
    for i, pct in enumerate(bands["pct"]):
        ax.text(i, pct + 0.5, f"{pct}%", ha="center", fontsize=9)
    ax.set_ylabel("% of transfer students")
    ax.set_xlabel("Credits transferred at admission (UFV excluded)")
    ax.set_title("How much credit transfer students arrive with")
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    _save(fig, "credit_bands")


def plot_avg_credits(avg_credits, chart_dir):
    """Average credits transferred, by receiving institution."""
    data = avg_credits.sort_values("avg_credits", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.barh(data["receiver"], data["avg_credits"], color="#1F4E79")
    ax.axvline(OVERALL_AVG_CREDITS, color="#C55A11", linestyle="--",
               label=f"Overall average ({OVERALL_AVG_CREDITS})")
    for i, value in enumerate(data["avg_credits"]):
        ax.text(value + 1, i, f"{value:.1f}", va="center", fontsize=9)
    ax.set_xlabel("Average credits transferred at admission (UFV excluded)")
    ax.set_title("Who arrives with the most credit: by receiving institution")
    ax.legend()
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    _save(fig, "avg_credits_by_receiver")


def main():
    by_year = load("transfer_by_year.csv")
    by_receiver = load("transfer_by_receiver.csv")
    by_region = load("transfer_by_region.csv")
    bands = load("credit_bands.csv")
    avg_credits = load("avg_credits_by_receiver.csv")
    completion = load("completion_by_receiver.csv")
    senders = load("top_senders.csv")

    yearly = compute_yearly(by_year)
    by_receiver = compute_receiver_shares(by_receiver)
    findings = summarise(yearly, by_receiver, by_region, bands, avg_credits,
                         completion, senders)
    print_findings(findings)

    os.makedirs(CHART_DIR, exist_ok=True)
    plot_executive_summary(yearly, CHART_DIR)
    plot_by_receiver(by_receiver, CHART_DIR)
    plot_credit_bands(bands, CHART_DIR)
    plot_avg_credits(avg_credits, CHART_DIR)
    print("Charts written to", CHART_DIR)


if __name__ == "__main__":
    main()
