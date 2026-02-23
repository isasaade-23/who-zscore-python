"""
WHO Growth Reference 2007 — Z-score Calculator (5-19 years)
============================================================

Calculates BMI-for-age and Height-for-age z-scores using the LMS method
with the WHO Reference 2007 for school-age children and adolescents.

Reference:
    de Onis M, et al. Development of a WHO growth reference for school-aged
    children and adolescents. Bull World Health Organ. 2007;85:660-667.

LMS tables source:
    WHO official R package 'anthroplus' (WorldHealthOrganization/anthroplus)
    https://github.com/WorldHealthOrganization/anthroplus

Formula:
    z = ((X/M)^L - 1) / (L * S)    when L ≠ 0
    z = ln(X/M) / S                 when L = 0

    For BMI-for-age (weight-based indicator), WHO applies a restricted
    approach for |z| > 3 to avoid assumptions beyond observed data:
        z > 3:  z_adj = 3 + (X - SD3pos) / (SD3pos - SD2pos)
        z < -3: z_adj = -3 + (X - SD3neg) / (SD2neg - SD3neg)

Age range: 61-228 months (5-19 years)
    Note: Tables include month 60 but this module uses 61+ to avoid
    overlap with WHO Child Growth Standards (0-60 months).

Sex coding: 1 = male, 2 = female

Usage:
    import pandas as pd
    from who_zscore import calc_who_zscore

    # Single calculation
    z = calc_who_zscore(bmi=18.5, age_months=100, sex=1, indicator='bfa')

    # Vectorized (DataFrame)
    df['zbmi'] = df.apply(lambda r: calc_who_zscore(
        r['bmi'], r['age'], r['sex'], 'bfa'), axis=1)

Dependencies:
    pandas, numpy

Author: Isa (USP) & Claude (Anthropic) — ECLS-K:2011 Obesity Project
Date: February 2026
"""

import os
import numpy as np
import pandas as pd

# ── Load LMS tables ──────────────────────────────────────────────────────
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

_bfa_table = pd.read_csv(os.path.join(_MODULE_DIR, "who_bmi_for_age_lms.csv"))
_hfa_table = pd.read_csv(os.path.join(_MODULE_DIR, "who_height_for_age_lms.csv"))

# Pre-index for fast lookup
_bfa_table = _bfa_table.set_index(["sex", "age"])
_hfa_table = _hfa_table.set_index(["sex", "age"])


def _lookup_lms(sex, age_months, indicator="bfa"):
    """Look up L, M, S values from WHO reference table."""
    table = _bfa_table if indicator == "bfa" else _hfa_table

    age_int = int(round(age_months))

    # Valid range: 61-228 months (5y1m to 19y0m)
    if age_int < 61 or age_int > 228:
        return None

    sex_int = int(sex)
    if sex_int not in (1, 2):
        return None

    try:
        row = table.loc[(sex_int, age_int)]
        return float(row["l"]), float(row["m"]), float(row["s"])
    except KeyError:
        return None


def calc_who_zscore(measurement, age_months, sex, indicator="bfa"):
    """
    Calculate WHO z-score using LMS method (Growth Reference 2007).

    Parameters
    ----------
    measurement : float
        BMI in kg/m² (indicator='bfa') or height in cm (indicator='hfa')
    age_months : float
        Age in months (will be rounded to nearest integer for lookup)
    sex : int
        1 = male, 2 = female
    indicator : str
        'bfa' = BMI-for-age, 'hfa' = height-for-age

    Returns
    -------
    float
        Z-score, or NaN if inputs are invalid/out of range
    """
    # Handle missing
    if pd.isna(measurement) or pd.isna(age_months) or pd.isna(sex):
        return np.nan

    if float(measurement) <= 0:
        return np.nan

    # Lookup LMS
    lms = _lookup_lms(sex, age_months, indicator)
    if lms is None:
        return np.nan

    L, M, S = lms
    X = float(measurement)

    # Standard LMS formula
    if L != 0:
        z = (((X / M) ** L) - 1) / (L * S)
    else:
        z = np.log(X / M) / S

    # WHO restricted approach for weight-based indicators (BMI-for-age)
    # Corrects z-scores beyond ±3 SD to avoid distribution assumptions
    if indicator == "bfa" and abs(z) > 3:
        if L != 0:
            SD3pos = M * (1 + L * S * 3) ** (1 / L)
            SD3neg = M * (1 + L * S * (-3)) ** (1 / L)
            SD2pos = M * (1 + L * S * 2) ** (1 / L)
            SD2neg = M * (1 + L * S * (-2)) ** (1 / L)
        else:
            SD3pos = M * np.exp(S * 3)
            SD3neg = M * np.exp(S * (-3))
            SD2pos = M * np.exp(S * 2)
            SD2neg = M * np.exp(S * (-2))

        if z > 3:
            SD23pos = SD3pos - SD2pos
            z = 3 + (X - SD3pos) / SD23pos
        elif z < -3:
            SD23neg = SD2neg - SD3neg
            z = -3 + (X - SD3neg) / SD23neg

    return round(z, 2)


def calc_who_zscore_series(df, bmi_col, height_col, age_col, sex_col):
    """
    Calculate z-scores for an entire DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
    bmi_col : str
        Column name for BMI values
    height_col : str
        Column name for height values (cm)
    age_col : str
        Column name for age in months
    sex_col : str
        Column name for sex (1=M, 2=F)

    Returns
    -------
    pd.DataFrame
        Original df with two new columns: 'zbmi' and 'zhfa'
    """
    df = df.copy()

    df["zbmi"] = df.apply(
        lambda r: calc_who_zscore(r[bmi_col], r[age_col], r[sex_col], "bfa"),
        axis=1,
    )

    df["zhfa"] = df.apply(
        lambda r: calc_who_zscore(r[height_col], r[age_col], r[sex_col], "hfa"),
        axis=1,
    )

    return df


# ── Self-test (run as script) ────────────────────────────────────────────
if __name__ == "__main__":
    print("WHO Growth Reference 2007 — Z-score Calculator")
    print("=" * 55)
    print("\nValidation against R anthroplus (WHO official package):")
    print(f"  {'Test':<30} {'Python':>8} {'R':>8} {'Match':>6}")
    print(f"  {'-'*55}")

    tests = [
        ("Boy 100mo BMI=30 (bfa)", 30, 100, 1, "bfa", 5.03),
        ("Boy 100mo ht=100 (hfa)", 100, 100, 1, "hfa", -5.04),
        ("Girl 110mo ht=90 (hfa)", 90, 110, 2, "hfa", -7.06),
    ]

    all_pass = True
    for desc, meas, age, sex, ind, expected in tests:
        result = calc_who_zscore(meas, age, sex, ind)
        match = abs(result - expected) < 0.02
        all_pass = all_pass and match
        print(f"  {desc:<30} {result:>8.2f} {expected:>8.2f} {'✅' if match else '❌':>6}")

    print(f"\n  {'ALL TESTS PASSED ✅' if all_pass else 'SOME TESTS FAILED ❌'}")
    print(f"\n  Age range: 61-228 months (5y1m to 19y0m)")
    print(f"  Sex: 1=male, 2=female")
    print(f"  Indicators: bfa (BMI-for-age), hfa (height-for-age)")
