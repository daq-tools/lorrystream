# Copyright (c) 2013-2023, The Kotori developers and contributors.
# Distributed under the terms of the LGPLv3 license, see LICENSE.

import json
import sys
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


def get_sqlalchemy_dialects() -> t.List[str]:
    """
    Return list of available SQLAlchemy dialects.

    :return:
    """
    from importlib.metadata import entry_points

    import sqlalchemy.dialects

    builtins = sqlalchemy.dialects.__all__
    more: t.List
    if sys.version_info >= (3, 10):
        eps = entry_points(group="sqlalchemy.dialects")
        more = [dialect.name for dialect in eps]
    else:
        eps = entry_points()
        more = [dialect[0].name for dialect in eps.values() if dialect[0].group == "sqlalchemy.dialects"]

    return sorted(list(builtins) + list(more))


def asbool(obj: t.Any) -> bool:
    # from sqlalchemy.util.langhelpers
    # from paste.deploy.converters
    if isinstance(obj, str):
        obj = obj.strip().lower()
        if obj in ["true", "yes", "on", "y", "t", "1"]:
            return True
        elif obj in ["false", "no", "off", "n", "f", "0"]:
            return False
        else:
            raise ValueError("String is not true/false: %r" % obj)
    return bool(obj)


def split_list(value: str, delimiter: str = ",") -> t.List[str]:
    if value is None:
        return []
    return [c.strip() for c in value.split(delimiter)]
