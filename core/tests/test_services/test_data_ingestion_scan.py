'''
Copyright 2019-Present The OpenUBA Platform Authors
data-ingestion dataset-scan tests (issue #35)

verifies that ingest_all_datasets discovers any real dataset under
TEST_DATASETS_PATH (not just toy_1) while skipping non-dataset directories.
No Spark/ES/DB needed — the physical ingest is mocked.
'''

from unittest.mock import MagicMock, patch

import pytest

from core.services.data_ingestion import DataIngestionService


def _make_tree(root):
    '''a test_datasets/ tree with two real datasets, a junk dir, and a stray file'''
    (root / "toy_1" / "proxy").mkdir(parents=True)
    (root / "toy_1" / "proxy" / "bluecoat.log").write_text("x\n")
    (root / "synth_x" / "ssh").mkdir(parents=True)
    (root / "synth_x" / "ssh" / "ssh.log").write_text("x\n")
    (root / "empty_dir").mkdir()               # no log-type subdirs → skipped
    (root / "labels.json").write_text("{}")    # a file, not a dir → skipped
    (root / ".hidden").mkdir()                 # hidden → skipped


def test_ingest_all_discovers_every_real_dataset(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_DATASETS_PATH", str(tmp_path))
    _make_tree(tmp_path)

    svc = DataIngestionService()
    # avoid any real Spark/ES work — record which datasets get ingested
    svc.ingest_from_test_datasets = MagicMock(return_value={"status": "success"})

    result = svc.ingest_all_datasets(ingest_to_spark=False, ingest_to_es=False)

    ingested = {c.kwargs.get("dataset_name") or c.args[0]
                for c in svc.ingest_from_test_datasets.call_args_list}
    assert ingested == {"toy_1", "synth_x"}          # both real datasets
    assert "empty_dir" not in ingested               # junk dir skipped
    assert result["total_datasets"] == 2


def test_toy_1_still_ingests_alone(tmp_path, monkeypatch):
    '''back-compat: a tree with only toy_1 behaves exactly as before'''
    monkeypatch.setenv("TEST_DATASETS_PATH", str(tmp_path))
    (tmp_path / "toy_1" / "dns").mkdir(parents=True)
    (tmp_path / "toy_1" / "dns" / "dns.log").write_text("x\n")

    svc = DataIngestionService()
    svc.ingest_from_test_datasets = MagicMock(return_value={"status": "success"})
    result = svc.ingest_all_datasets(ingest_to_spark=False, ingest_to_es=False)

    assert result["total_datasets"] == 1
    svc.ingest_from_test_datasets.assert_called_once()
    call = svc.ingest_from_test_datasets.call_args
    assert (call.kwargs.get("dataset_name") or call.args[0]) == "toy_1"
