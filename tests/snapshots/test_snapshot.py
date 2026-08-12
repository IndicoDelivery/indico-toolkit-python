import os
import tempfile
from copy import deepcopy

import pytest

from indico_toolkit.errors import ToolkitInputError
from indico_toolkit.snapshots import Snapshot

pd = pytest.importorskip("pandas")

# TODO: tests for exception handling


@pytest.fixture
def snapshot_classes():
    snapshot_classes = [
        "Grand Total Due",
        "Line Cost",
        "Line Description",
        "Quantity",
        "Sub Total",
        "Tax",
        "Transaction Date",
        "Transaction Time",
        "Vendor City",
        "Vendor Name",
        "Vendor State",
        "Vendor Street Address",
        "Vendor Zip Code",
    ]
    return snapshot_classes


def test_instantiation_wo_params(snapshot_file):
    snap = Snapshot(snapshot_file)
    assert snap.text_col == "document"
    assert snap.label_col == "question"
    assert snap.file_name_col == "file_name_10765"
    assert isinstance(snap.df[snap.label_col].iloc[0]["targets"], list)


def test_instantiation(snapshot_file):
    snap = Snapshot(
        snapshot_file,
        text_col="document",
        label_col="question",
        file_name_col="file_name_10765",
    )
    assert snap.text_col == "document"
    assert snap.label_col == "question"
    assert snap.file_name_col == "file_name_10765"
    assert isinstance(snap.df[snap.label_col].iloc[0]["targets"], list)


def test_instantiation_bad_label_col(snapshot_file):
    with pytest.raises(ToolkitInputError):
        Snapshot(
            snapshot_file,
            label_col="file_name_10765",
        )


def test_remove_extraction_labels(snapshot_file):
    snap = Snapshot(snapshot_file)
    assert "Vendor Name" in [
        i["label"] for i in snap.df[snap.label_col].iloc[0]["targets"]
    ]
    snap.remove_extraction_labels(["Vendor Name"])
    assert "Vendor Name" not in [
        i["label"] for i in snap.df[snap.label_col].iloc[0]["targets"]
    ]


def test_standardize_names(snapshot_file):
    snap = Snapshot(snapshot_file)
    snap.standardize_column_names()
    assert "source" and "target" and "file_name" in snap.df.columns


def test__eq__not_equal(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    with pytest.raises(AssertionError):
        assert snap1 == snap2


def test__eq__(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    assert snap1 == snap2


def test_append(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap1.append(snap2)
    expected_length = snap2.df.shape[0] * 2
    assert snap1.df.shape[0] == expected_length


def test_to_csv(snapshot_file):
    snap = Snapshot(snapshot_file)
    snap.standardize_column_names()
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        snap.to_csv(tf.name)
        df = pd.read_csv(tf.name)
        assert df.shape[1] == 3
        assert isinstance(df["target"][0], str)


def test_split_and_write_to_csv(snapshot_file):
    snap = Snapshot(snapshot_file)
    with tempfile.TemporaryDirectory() as dirpath:
        snap.split_and_write_to_csv(dirpath, num_splits=3, output_base_name="my_split")
        original = pd.read_csv(snapshot_file)
        assert original.shape[0] == 10  # / 3 = 3,3,4
        df1 = pd.read_csv(os.path.join(dirpath, "my_split_1.csv"))
        df2 = pd.read_csv(os.path.join(dirpath, "my_split_2.csv"))
        df3 = pd.read_csv(os.path.join(dirpath, "my_split_3.csv"))
        assert df1.shape[0] == 3
        assert df2.shape[0] == 3
        assert df3.shape[0] == 4
        full = pd.concat([df1, df2, df3]).reset_index(drop=True)
        assert full.shape[0] == original.shape[0]
        assert set(full.columns) == set(original.columns)
        assert set(full["document"].tolist()) == set(original["document"].tolist())


def test_merge_by_file_name(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap1.merge_by_file_name(snap2)
    expected_pred_length = len(snap2.df[snap2.label_col][0]["targets"]) * 2
    assert len(snap1.df[snap1.label_col][0]["targets"]) == expected_pred_length
    assert snap1.df.shape[0] == snap2.df.shape[0]
    for val in snap1.df[snap1.label_col]:
        assert isinstance(val, dict)


def test_merge_by_file_name_columns_no_match(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    with pytest.raises(ToolkitInputError):
        snap1.merge_by_file_name(snap2)


def test_merge_by_file_name_no_filename_matches(snapshot_file):
    snap1 = Snapshot(snapshot_file)
    snap2 = Snapshot(snapshot_file)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap2.df[snap2.file_name_col] = "no_match"
    original_labels = deepcopy(snap1.df[snap1.label_col].tolist())
    snap1.merge_by_file_name(snap2)
    assert snap1.df[snap1.label_col].tolist() == original_labels


def test_get_extraction_label_names(snapshot_file, snapshot_classes):
    snap = Snapshot(snapshot_file)
    label_list = snap.get_extraction_label_names()
    assert len(snapshot_classes) == len(label_list)
    for snapshot_class, test_class in zip(snapshot_classes, label_list):
        assert snapshot_class == test_class


def test_number_of_samples(snapshot_file):
    snap = Snapshot(snapshot_file)
    assert snap.number_of_samples == 10


def test_get_all_labeled_text(snapshot_file):
    snap = Snapshot(snapshot_file)
    labeled_text = snap.get_all_labeled_text("Vendor State")
    assert len(labeled_text) == 10
    assert isinstance(labeled_text[0], str)
    assert labeled_text[0] == "WY"


def test_get_all_labeled_text_per_doc(snapshot_file):
    snap = Snapshot(snapshot_file)
    labeled_text = snap.get_all_labeled_text("Vendor State", return_per_document=True)
    assert len(labeled_text) == 10
    assert isinstance(labeled_text[0], list)
    assert len(labeled_text[0]) == 1
    assert labeled_text[0][0] == "WY"


def test_update_label_col_format(old_snapshot_file):
    snap = Snapshot(old_snapshot_file)
    old_df = deepcopy(snap.df)
    snap.update_label_col_format(task_type="annotation")

    assert old_df.shape == snap.shape
    assert snap.df[snap.label_col].iloc[0]["task_type"] == "annotation"
    assert isinstance(snap.df[snap.label_col].iloc[0]["targets"], list)

    for i, snapshot in enumerate(snap.df[snap.label_col]):
        assert len(old_df[snap.label_col].iloc[i]) == len(snapshot["targets"])
