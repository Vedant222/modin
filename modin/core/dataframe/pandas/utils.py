# Licensed to Modin Development Team under one or more contributor license agreements.
# See the NOTICE file distributed with this work for additional information regarding
# copyright ownership.  The Modin Development Team licenses this file to you under the
# Apache License, Version 2.0 (the "License"); you may not use this file except in
# compliance with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.


"""Collection of utility functions for the PandasDataFrame."""

import pandas
from pandas.api.types import union_categoricals


def concatenate(dfs):
    """
    Concatenate pandas DataFrames with saving 'category' dtype.

    All dataframes' columns must be equal to each other.

    Parameters
    ----------
    dfs : list
        List of pandas DataFrames to concatenate.

    Returns
    -------
    pandas.DataFrame
        A pandas DataFrame.
    """
    for df in dfs:
        assert df.columns.equals(dfs[0].columns)
    for i in dfs[0].columns.get_indexer_for(dfs[0].select_dtypes("category").columns):
        columns = [df.iloc[:, i] for df in dfs]
        all_categorical_parts_are_empty = None
        has_non_categorical_parts = False
        for col in columns:
            if isinstance(col.dtype, pandas.CategoricalDtype):
                if all_categorical_parts_are_empty is None:
                    all_categorical_parts_are_empty = len(col) == 0
                    continue
                all_categorical_parts_are_empty &= len(col) == 0
            else:
                has_non_categorical_parts = True
        # 'union_categoricals' raises an error if some of the passed values don't have categorical dtype,
        # if it happens, we only want to continue when all parts with categorical dtypes are actually empty.
        # This can happen if there were an aggregation that discards categorical dtypes and that aggregation
        # doesn't properly do so for empty partitions
        if has_non_categorical_parts and all_categorical_parts_are_empty:
            continue
        union = union_categoricals(columns)
        for df in dfs:
            df.isetitem(
                i, pandas.Categorical(df.iloc[:, i], categories=union.categories)
            )
    # `ValueError: buffer source array is read-only` if copy==False
    if len(dfs) == 1:
        # concat doesn't make a copy if len(dfs) == 1,
        # so do it explicitly
        return dfs[0].copy()
    return pandas.concat(dfs, copy=True)
