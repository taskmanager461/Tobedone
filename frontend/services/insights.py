from __future__ import annotations

import pandas as pd
from typing import Any


def build_weekly_insight(weekly_df: pd.DataFrame, weekly_success: float, t: Any) -> tuple[str, str]:
    avg_score = float(weekly_df["score"].mean()) if not weekly_df.empty else 0.0
    score_delta = float(weekly_df["score"].iloc[-1] - weekly_df["score"].iloc[0]) if len(weekly_df) > 1 else 0.0

    if weekly_success >= 75 and score_delta >= 0 and avg_score >= 20:
        insight = t("insight_strong")
        tip = t("score_insight_tip_3")
    elif weekly_success >= 55 or score_delta > 0:
        insight = t("insight_solid")
        tip = t("score_insight_tip_1")
    else:
        insight = t("insight_recovery")
        tip = t("score_insight_tip_2")
    return insight, t("insight_next_step", tip=tip)
