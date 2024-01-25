import functools
import os
from typing import List, Callable, Dict, Optional

import pandas as pd
import swifter

import logging

logger = logging.getLogger("AutoRAG")


def fetch_contents(corpus_data: pd.DataFrame, ids: List[List[str]]) -> List[List[str]]:
    assert isinstance(ids[0], list), "ids must be a list of list of ids."
    id_df = pd.DataFrame(ids, columns=[f'id_{i}' for i in range(len(ids[0]))])
    try:
        contents_df = id_df.swifter.applymap(
            lambda x: corpus_data.loc[lambda row: row['doc_id'] == x]['contents'].values[0])
    except IndexError:
        logger.error(f"doc_id does not exist in corpus_data.")
        raise IndexError("doc_id does not exist in corpus_data.")
    return contents_df.values.tolist()


def result_to_dataframe(column_names: List[str]):
    """
    Decorator for converting results to pd.DataFrame.
    """

    def decorator_result_to_dataframe(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> pd.DataFrame:
            results = func(*args, **kwargs)
            df_input = {column_name: result for result, column_name in zip(results, column_names)}
            result_df = pd.DataFrame(df_input)
            return result_df

        return wrapper

    return decorator_result_to_dataframe


def make_module_file_name(module_name: str, module_params: Dict) -> str:
    """
    Make module parquet file name for saving results dataframe.

    :param module_name: Module name.
        It can be module function's name.
    :param module_params: Parameters of the module function.
    :return: Module parquet file name
    """
    module_params_str = "-".join(list(map(lambda x: f"{x[0]}_{x[1]}", module_params.items())))
    if len(module_params_str) <= 0:
        return f"{module_name}.parquet"
    return f"{module_name}=>{module_params_str}.parquet"


def find_best_result_path(node_dir: str) -> str:
    """
    Find the best result filepath from node directory.
    :param node_dir: The directory of the node.
    :return: The filepath of the best result.
    """
    return list(filter(lambda x: x.endswith(".parquet") and x.startswith("best_"), os.listdir(node_dir)))[0]


def load_summary_file(summary_path: str,
                      dict_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load summary file from summary_path.

    :param summary_path: The path of the summary file.
    :param dict_columns: The columns that are dictionary type.
        You must fill this parameter if you want to load summary file properly.l
        Default is None.
    :return: The summary dataframe.
    """
    if not os.path.exists(summary_path):
        raise ValueError(f"summary.parquet does not exist in {summary_path}.")
    summary_df = pd.read_parquet(summary_path)
    if dict_columns is None:
        logger.warning("dict_columns is None."
                       "If your input summary_df has dictionary type columns, you must fill dict_columns.")
        return summary_df

    def delete_none_at_dict(elem):
        return dict(filter(lambda item: item[1] is not None, elem.items()))

    summary_df[dict_columns] = summary_df[dict_columns].applymap(delete_none_at_dict)
    return summary_df