# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the GPLv3 license, see LICENSE.

import json
import typing as t

import pandas as pd


def jd(data: t.Any):
    """
    Pretty-print JSON with indentation.
    """
    print(json.dumps(data, indent=2))  # noqa: T201


def chunker(seq: pd.DataFrame, chunksize: int):
    """
    Chunks generator function for iterating pandas Dataframes and Series.

    https://stackoverflow.com/a/61798585
    :return:
    """
    for pos in range(0, len(seq), chunksize):
        yield seq.iloc[pos : pos + chunksize]


def df_convert_datetimes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert all datetime columns to ISO format.

    :param df:        df[Columns.FROM_DATE] = df[Columns.FROM_DATE].dt.tz_localize(self.tz)
    :return:
    """
    df = df.copy(deep=True)

    date_columns = list(df.select_dtypes(include=[pd.DatetimeTZDtype]).columns)
    # date_columns.extend([Columns.FROM_DATE.value, Columns.TO_DATE.value, Columns.DATE.value])  # noqa: ERA001
    date_columns_set = set(date_columns)
    for date_column in date_columns_set:
        if date_column in df:
            df[date_column] = df[date_column].apply(lambda d: d.isoformat() if pd.notna(d) else None)

    return df
