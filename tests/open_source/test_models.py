import os
from mlflow_export_import.common.source_tags import ExportTags
from mlflow_export_import.common import MlflowExportImportException
from mlflow_export_import.model.export_model import ModelExporter
from mlflow_export_import.model.import_model import ModelImporter
from mlflow_export_import.model.import_model import _extract_model_path, _path_join

import oss_utils_test 
from compare_utils import compare_models_with_versions, compare_models, compare_versions
from init_tests import mlflow_context


# Test stages

def test_export_import_model_1_stage(mlflow_context):
    model_src, model_dst = _run_test_export_import_model_stages(mlflow_context, stages=["Production"] )
    assert len(model_dst.latest_versions) == 1
    compare_models_with_versions(mlflow_context.client_src, mlflow_context.client_dst,  model_src, model_dst, mlflow_context.output_dir)


def test_export_import_model_2_stages(mlflow_context):
    model_src, model_dst = _run_test_export_import_model_stages(mlflow_context, stages=["Production","Staging"])
    assert len(model_dst.latest_versions) == 2
    compare_models_with_versions(mlflow_context.client_src, mlflow_context.client_dst,  model_src, model_dst, mlflow_context.output_dir)


def test_export_import_model_all_stages(mlflow_context):
    model_src, model_dst = _run_test_export_import_model_stages(mlflow_context, stages=None)
    assert len(model_dst.latest_versions) == 4
    compare_models_with_versions(mlflow_context.client_src, mlflow_context.client_dst,  model_src, model_dst, mlflow_context.output_dir)


# Test stages and versions

def test_export_import_model_both_stages(mlflow_context):
    try:
        _run_test_export_import_model_stages(mlflow_context,  stages=["Production"], versions=[1])
    except MlflowExportImportException:
        # "Both stages {self.stages} and versions {self.versions} cannot be set")
        pass


# Test versions

def _get_version_ids(model):
    return [vr.version for vr in model.latest_versions ]


def _get_version_ids_dst(model):
    return [vr.tags[f"{ExportTags.PREFIX_FIELD}.version"] for vr in model.latest_versions ]


def test_export_import_model_first_two_versions(mlflow_context):
    model_src, model_dst = _run_test_export_import_model_stages(mlflow_context, versions=["1","2"])
    assert len(model_dst.latest_versions) == 2
    compare_models_with_versions(mlflow_context.client_src, mlflow_context.client_dst,  model_src, model_dst, mlflow_context.output_dir)
    ids_src = _get_version_ids(model_src)
    ids_dst = _get_version_ids(model_dst)
    for j, id in enumerate(ids_dst):
        assert(id == ids_src[j])


def test_export_import_model_two_from_middle_versions(mlflow_context):
    model_src, model_dst = _run_test_export_import_model_stages(mlflow_context, versions=["2","3","4"])
    assert len(model_dst.latest_versions) == 3
    ids_src = _get_version_ids(model_src)
    ids_dst = _get_version_ids_dst(model_dst)
    assert set(ids_dst).issubset(set(ids_src))

    compare_models(model_src, model_dst, mlflow_context.client_src!=mlflow_context.client_dst)
    for vr_dst in model_dst.latest_versions:
        vr_src_id = vr_dst.tags[f"{ExportTags.PREFIX_FIELD}.version"]
        vr_src = [vr for vr in model_src.latest_versions if vr.version == vr_src_id ]
        assert(len(vr_src)) == 1
        vr_src = vr_src[0]
        assert(vr_src.version == vr_src_id)
        compare_versions(mlflow_context.client_src, mlflow_context.client_dst, vr_src, vr_dst, mlflow_context.output_dir)


# Internal

def _run_test_export_import_model_stages(mlflow_context, stages=None, versions=None):
    exporter = ModelExporter(mlflow_context.client_src, stages=stages, versions=versions)
    model_name_src = oss_utils_test.mk_test_object_name_default()
    desc = "Hello decription"
    tags = { "city": "franconia" }
    model_src = mlflow_context.client_src.create_registered_model(model_name_src, tags, desc)

    _create_version(mlflow_context.client_src, model_name_src, "Production")
    _create_version(mlflow_context.client_src, model_name_src, "Staging")
    _create_version(mlflow_context.client_src, model_name_src, "Archived")
    _create_version(mlflow_context.client_src, model_name_src, "None")
    model_src = mlflow_context.client_src.get_registered_model(model_name_src)
    exporter.export_model(model_name_src, mlflow_context.output_dir)

    model_name_dst = oss_utils_test.create_dst_model_name(model_name_src)
    experiment_name =  model_name_dst
    importer = ModelImporter(mlflow_context.client_dst, import_source_tags=True)
    importer.import_model(model_name_dst, 
        mlflow_context.output_dir, 
        experiment_name, delete_model=True, 
        verbose=False, 
        sleep_time=10)

    model_dst = mlflow_context.client_dst.get_registered_model(model_name_dst)
    return model_src, model_dst


def _create_version(client, model_name, stage=None):
    run = _create_run(client)
    source = f"{run.info.artifact_uri}/model"
    desc = "My version desc"
    tags = { "city": "franconia" }
    vr = client.create_model_version(model_name, source, run.info.run_id, description=desc, tags=tags)
    if stage:
        vr = client.transition_model_version_stage(model_name, vr.version, stage)
    return vr


def _create_run(client):
    _, run = oss_utils_test.create_simple_run(client)
    return client.get_run(run.info.run_id)


# Parsing test for _extract_model_path to extract from version `source` field

_exp_id = "1812"
_run_id = "48cf29167ddb4e098da780f0959fb4cf"
_local_path_base = os.path.join("dbfs:/databricks/mlflow-tracking", _exp_id, _run_id)


def test_extract_no_artifacts():
    source = os.path.join(_local_path_base)
    model_path = _extract_model_path(source, _run_id)
    assert model_path == ""


def test_extract_just_artifacts():
    source = os.path.join(_local_path_base, "artifacts")
    model_path = _extract_model_path(source, _run_id)
    assert model_path == ""


def test_extract_just_artifacts_slash():
    source = os.path.join(_local_path_base, "artifacts/")
    model_path = _extract_model_path(source, _run_id)
    assert model_path == ""


def test_extract_model():
    source = os.path.join(_local_path_base, "artifacts","model")
    model_path = _extract_model_path(source, _run_id)
    assert model_path == "model"


def test_extract_model_sklearn():
    source = os.path.join(_local_path_base, "artifacts","model/sklearn")
    model_path = _extract_model_path(source, _run_id)
    assert model_path == "model/sklearn"


def _test_extract_no_run_id():
    source = os.path.join(_local_path_base, "artifacts")
    try:
        _extract_model_path(source, "1215")
        assert False
    except MlflowExportImportException:
        pass


# == Test for DOS path adjustment

_base_dir = "dbfs:/mlflow/1812"
_expected_path = "dbfs:/mlflow/1812/model"

def test_path_join_frontslash():
    res = _path_join(_base_dir, "model")
    assert res == os.path.join(_expected_path)

def test_path_join_backslash():
    dir = _base_dir.replace("/","\\")
    res = _path_join(dir, "model")
    assert res == os.path.join(_expected_path)
