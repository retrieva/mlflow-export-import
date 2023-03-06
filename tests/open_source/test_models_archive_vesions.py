"""
Tests for 'archive_existing_versions' in transition_model_version_stage()
See: https://mlflow.org/docs/latest/python_api/mlflow.client.html#mlflow.client.MlflowClient.transition_model_version_stage
"""

from mlflow_export_import.model.export_model import ModelExporter
from mlflow_export_import.model.import_model import ModelImporter
from mlflow_export_import.common.model_utils import list_model_versions

import oss_utils_test 
from init_tests import mlflow_context
from compare_utils import compare_models, compare_versions

# == Test with archive_existing_versions=False (default)

# Test one version with one stage

def test_1_prod_archive_no(mlflow_context):
    _run_test(mlflow_context, "Production", 1, False)

def test_1_staging_archive_no(mlflow_context):
    _run_test(mlflow_context, "Production", 1, False)

def test_1_stages_archived_archive_no(mlflow_context):
    _run_test(mlflow_context, "Archived", 1, False)

def test_1_none_archive_no(mlflow_context):
    _run_test(mlflow_context, "None", 1, False)

# Test two versions with same stage

def test_2_prod_archive_no(mlflow_context):
    _run_test(mlflow_context, "Production", 2, False)

def test_2_staging_archive_no(mlflow_context):
    _run_test(mlflow_context, "Staging", 2, False)

def test_2_archived_archive_no(mlflow_context):
    _run_test(mlflow_context, "Archived", 2, False)

def test_2_none_archive_no(mlflow_context):
    _run_test(mlflow_context, "None", 2, False)


# == Test with archive_existing_versions=True

# Test one version with one stage

def test_1_prod_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Production", 1, True)

def test_1_staging_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Production", 1, True)

# NOTE: Timeout when archive_existing_versions=True
# MaxRetryError: 'too many 500 error responses'
def _test_1_stages_archived_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Archived", 1, True)

# NOTE: ibid Timeout
def _test_1_none_archive_yes(mlflow_context):
    _run_test(mlflow_context, "None", 1, True)

# Test two versions with same stage

def test_2_prod_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Production", 2, True)

def test_2_staging_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Staging", 2, True)

# NOTE: ibid Timeout
def _test_2_archived_archive_yes(mlflow_context):
    _run_test(mlflow_context, "Archived", 2, True)

# NOTE: ibid Timeout
def _test_2_none_archive_yes(mlflow_context):
    _run_test(mlflow_context, "None", 2, True)


# == Helper functions

def _run_test(mlflow_context, stage, num_stages, archive_existing_versions=False):
    """ Run with one or mode same stages, i.e. ['Production', 'Production'] """
    stages = [ stage for _ in range(0,num_stages) ]
    model_src, model_dst = _run_export_import(mlflow_context, stages, archive_existing_versions)

    src_all_versions = list_model_versions(mlflow_context.client_src, model_src.name)
    if num_stages == 1:
        assert len(src_all_versions) == 1
        assert len(src_all_versions) == len(model_src.latest_versions)
    else:
        if archive_existing_versions:
            assert len(src_all_versions) == len(model_src.latest_versions)
        else:
            assert len(src_all_versions) > len(model_src.latest_versions)

    dst_all_versions = list_model_versions(mlflow_context.client_dst, model_dst.name)
    assert len(src_all_versions) == len(dst_all_versions)
    assert len(model_src.latest_versions) == len(model_dst.latest_versions)

    _compare_models_with_versions(mlflow_context.client_src, mlflow_context.client_dst, model_src, model_dst, mlflow_context.output_dir)


def _run_export_import(mlflow_context, stages, archive_existing_versions=False):
    exporter = ModelExporter(mlflow_context.client_src)
    model_name_src = oss_utils_test.mk_test_object_name_default()
    model_src = mlflow_context.client_src.create_registered_model(model_name_src)

    for stage in stages:
        _create_version(mlflow_context.client_src, model_name_src, stage, archive_existing_versions)

    model_src = mlflow_context.client_src.get_registered_model(model_name_src)
    exporter.export_model(model_name_src, mlflow_context.output_dir)

    model_name_dst = oss_utils_test.create_dst_model_name(model_name_src)
    experiment_name =  model_name_dst
    importer = ModelImporter(mlflow_context.client_dst, import_source_tags=True)
    importer.import_model(model_name_dst,
        mlflow_context.output_dir,
        experiment_name,
        delete_model=True,
        verbose=False,
        sleep_time=10)

    model_dst = mlflow_context.client_dst.get_registered_model(model_name_dst)
    return model_src, model_dst


def _create_version(client, model_name, stage=None, archive_existing_versions=False):
    run = _create_run(client)
    source = f"{run.info.artifact_uri}/model"
    vr = client.create_model_version(model_name, source, run.info.run_id, description="Hello", tags={"city": "Elk"})
    if stage:
        vr = client.transition_model_version_stage(model_name, vr.version, stage, archive_existing_versions)
    return vr


def _create_run(client):
    _, run = oss_utils_test.create_simple_run(client)
    return client.get_run(run.info.run_id)


def _compare_models_with_versions(mlflow_client_src, mlflow_client_dst, model_src, model_dst, output_dir):

    def _sort_versions(versions):
        return sorted(versions, key=lambda vr: vr.version)

    def _compare_version_lists(src_versions, dst_versions, output_dir):
        src_versions = _sort_versions(src_versions)
        dst_versions = _sort_versions(dst_versions)
        assert len(src_versions) == len(dst_versions)
        for (vr_src, vr_dst) in zip(src_versions, dst_versions):
            compare_versions(mlflow_client_src, mlflow_client_dst, vr_src, vr_dst, output_dir)

    compare_models(model_src, model_dst, mlflow_client_src!=mlflow_client_dst)
    _compare_version_lists(model_src.latest_versions, model_dst.latest_versions, output_dir)
    _compare_version_lists(
        list_model_versions(mlflow_client_src, model_src.name),
        list_model_versions(mlflow_client_dst, model_dst.name),
        output_dir)
