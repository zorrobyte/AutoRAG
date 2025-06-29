import os
import pathlib

import pandas as pd
import pytest

from autorag.data.legacy.qacreation.ragas import generate_qa_ragas
from autorag.utils import validate_qa_dataset

root_dir = pathlib.PurePath(
    os.path.dirname(os.path.realpath(__file__))
).parent.parent.parent.parent
resource_dir = os.path.join(root_dir, "resources")
corpus_df = pd.read_parquet(os.path.join(resource_dir, "corpus_data_sample.parquet"))


@pytest.mark.skip(reason="This test is deprecated and will be removed in the future.")
def test_generate_qa_ragas():
    qa_df = generate_qa_ragas(corpus_df, 3)
    assert len(qa_df) == 3
    validate_qa_dataset(qa_df)
    id_ = qa_df["retrieval_gt"].tolist()[0][0][0]
    assert isinstance(id_, str)
    assert id_ in corpus_df["doc_id"].tolist()
