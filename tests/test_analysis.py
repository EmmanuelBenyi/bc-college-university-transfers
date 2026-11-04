"""Tests for the BC college-to-university transfers analysis.

Two kinds of checks:
  * Transcription checks: the CSVs match the BCCAT report's own published
    totals (see SOURCES in the README for the table behind each file).
  * Computation checks: shares, peaks, and rankings computed from the
    tables behave as expected.
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import (PUBLISHED_TOTAL_TRANSFER, compute_receiver_shares,
                      compute_yearly)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data")


def _load(name):
    return pd.read_csv(os.path.join(DATA_DIR, name))


def test_yearly_values_match_table_total_row():
    """Yearly transfer figures equal Table 2's published total row.

    Note: those five yearly figures sum to 29,799, one more than the
    report's grand total of 29,798. The region totals (below) sum exactly
    to 29,798, so the one-student gap sits in the yearly row — consistent
    with the report's rounding of cells next to masked (<10) cells.
    """
    by_year = _load("transfer_by_year.csv")
    assert list(by_year["transfer"]) == [6070, 6340, 6830, 5585, 4974]
    assert list(by_year["direct_entry"]) == [14999, 14277, 14432, 14951, 15021]
    assert by_year["transfer"].sum() - PUBLISHED_TOTAL_TRANSFER == 1
    assert by_year["direct_entry"].sum() == 73680


def test_receiver_and_region_totals_match_grand_total():
    by_receiver = _load("transfer_by_receiver.csv")
    assert by_receiver["transfer"].sum() == PUBLISHED_TOTAL_TRANSFER
    assert by_receiver["direct_entry"].sum() == 73680
    by_region = _load("transfer_by_region.csv")
    assert by_region["total"].sum() == PUBLISHED_TOTAL_TRANSFER
    mainland = by_region.loc[by_region["region"] == "Mainland/Southwest",
                             "total"].iloc[0]
    assert mainland / PUBLISHED_TOTAL_TRANSFER == pytest.approx(0.713, abs=0.001)


def test_credit_bands_sum_and_ufv_gap():
    bands = _load("credit_bands.csv")
    assert bands["pct"].sum() == 100
    assert bands["count"].sum() == 28346
    # The credit-band tables exclude UFV (data unavailable); adding UFV's
    # 1,452 transfer students reconciles exactly to the grand total.
    assert bands["count"].sum() + 1452 == PUBLISHED_TOTAL_TRANSFER
    assert bands.loc[bands["band"] == "60-64", "pct"].iloc[0] == 20
    assert bands.loc[bands["band"] == "30-34", "pct"].iloc[0] == 17
    assert bands.loc[bands["band"] == "65+", "count"].iloc[0] == 2203


def test_avg_credits_extremes():
    avg = _load("avg_credits_by_receiver.csv")
    assert avg.loc[avg["avg_credits"].idxmax(), "receiver"] == "UNBC"
    assert avg["avg_credits"].max() == 69.0
    assert avg.loc[avg["avg_credits"].idxmin(), "receiver"] == "TRU"
    assert avg["avg_credits"].min() == 36.5
    assert len(avg) == 9  # UFV excluded (data unavailable)


def test_completion_graduates_and_rates():
    comp = _load("completion_by_receiver.csv")
    assert comp["graduates"].sum() == 4382
    # Derived admitted counts sum to 5,809 vs the published cohort of 5,802;
    # the 7-student gap is the report's rounding of cells next to masked cells.
    assert abs(comp["admitted_derived"].sum() - 5802) <= 10
    # Published percentages reproduce from graduates / derived admitted.
    for _, row in comp.iterrows():
        recomputed = row["graduates"] / row["admitted_derived"] * 100
        assert recomputed == pytest.approx(row["completion_pct"], abs=1.5)


def test_top_sender_pipeline():
    senders = _load("top_senders.csv")
    top = senders.iloc[0]
    assert top["sender"] == "Fraser International College"
    assert top["total"] == 4923
    assert top["top_receiver"] == "SFU"
    assert top["top_receiver_count"] == 4817
    assert top["top_receiver_count"] / top["total"] == pytest.approx(0.978, abs=0.001)


def test_yearly_share_peaks_in_2020_21():
    yearly = compute_yearly(_load("transfer_by_year.csv"))
    peak_share_year = yearly.loc[yearly["transfer_share_pct"].idxmax(), "year"]
    assert peak_share_year == "2020/21"
    assert yearly.loc[yearly["year"] == "2020/21",
                      "transfer_share_pct"].iloc[0] == pytest.approx(32.1, abs=0.1)


def test_receiver_shares():
    by_receiver = compute_receiver_shares(_load("transfer_by_receiver.csv"))
    sfu = by_receiver.loc[by_receiver["receiver"] == "SFU"].iloc[0]
    assert sfu["transfer_share_pct"] == pytest.approx(45.2, abs=0.1)
    rru = by_receiver.loc[by_receiver["receiver"] == "RRU"].iloc[0]
    assert rru["transfer_share_pct"] == pytest.approx(86.5, abs=0.1)
    unbc = by_receiver.loc[by_receiver["receiver"] == "UNBC"].iloc[0]
    assert unbc["transfer_share_pct"] == pytest.approx(50.7, abs=0.1)
