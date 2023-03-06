import os
from oss_utils_test import mk_test_object_name_default, list_experiments, delete_experiments_and_models
from compare_utils import compare_runs

from mlflow_export_import.bulk.export_models import export_models
from mlflow_export_import.bulk.import_models import import_all
from mlflow_export_import.bulk import bulk_utils
from test_bulk_experiments import create_test_experiment
from init_tests import mlflow_context

# == Setup

notebook_formats = "SOURCE,DBC"
num_models = 2
num_runs = 2

# == Compare

def compare_models_with_versions(mlflow_context, compare_func):
    test_dir = os.path.join(mlflow_context.output_dir, "test_compare_runs")
    exps = list_experiments(mlflow_context.client_src)
    exp_ids = [ exp.experiment_id for exp in exps ]
    models2 = mlflow_context.client_dst.search_registered_models()
    assert len(models2) > 0
    for model2 in models2:
        versions2 = mlflow_context.client_dst.get_latest_versions(model2.name)
        for vr in versions2:
            run2 = mlflow_context.client_dst.get_run(vr.run_id)
            tag = run2.data.tags["my_uuid"]
            filter = f"tags.my_uuid = '{tag}'"
            run1 = mlflow_context.client_src.search_runs(exp_ids, filter)[0]
            tdir = os.path.join(test_dir,run2.info.run_id)
            os.makedirs(tdir)
            assert run1.info.run_id != run2.info.run_id
            compare_func(mlflow_context.client_src, mlflow_context.client_dst, run1, run2, tdir)

# == Helper methods

def create_model(client):
    exp = create_test_experiment(client, num_runs)
    model_name = mk_test_object_name_default()
    model = client.create_registered_model(model_name)
    for run in client.search_runs([exp.experiment_id]):
        source = f"{run.info.artifact_uri}/model"
        client.create_model_version(model_name, source, run.info.run_id)
    return model.name

def _run_test(mlflow_context, compare_func, use_threads=False):
    delete_experiments_and_models(mlflow_context)
    model_names = [ create_model(mlflow_context.client_src) for j in range(0,num_models) ]
    export_models(mlflow_context.client_src,
        model_names, 
        mlflow_context.output_dir, 
        notebook_formats, 
        stages="None", 
        export_all_runs=False, 
        use_threads=False)

    import_all(mlflow_context.client_dst,
        mlflow_context.output_dir,
        delete_model=False,
        use_src_user_id=False,
        verbose=False,
        use_threads=use_threads)

    compare_models_with_versions(mlflow_context, compare_func)

# == Export/import registered model tests

def test_basic(mlflow_context):
    _run_test(mlflow_context, compare_runs)

def test_exp_basic_threads(mlflow_context):
    _run_test(mlflow_context, compare_runs, use_threads=True)

def test_exp_with_source_tags(mlflow_context):
    _run_test(mlflow_context, compare_runs)

# == Test number if all runs of an experiment or just those of the version are exported

def _add_version(client, model_name, run, stage):
    source = f"{run.info.artifact_uri}/model"
    vr = client.create_model_version(model_name, source, run.info.run_id)
    client.transition_model_version_stage(model_name, vr.version, stage)

def _export_models(client, model_name, output_dir, export_all_runs):
    export_models(client, [ model_name ],
        output_dir, 
        stages="production,staging",
        export_all_runs=export_all_runs
    )

_num_runs1, _num_runs2 = (2, 3)

def _run_test_export_runs(mlflow_context, export_all_runs):
    delete_experiments_and_models(mlflow_context)
    client1 = mlflow_context.client_src
    exp1 = create_test_experiment(client1, _num_runs1)
    exp2 = create_test_experiment(client1, _num_runs2)
    model_name = mk_test_object_name_default()
    client1.create_registered_model(model_name)

    runs1 = client1.search_runs([exp1.experiment_id])
    _add_version(client1, model_name, runs1[0], "production")
    runs2 = client1.search_runs([exp2.experiment_id])
    _add_version(client1, model_name, runs2[0], "staging")
    client1.get_latest_versions(model_name)

    _export_models(client1, model_name, mlflow_context.output_dir, export_all_runs)
    
    client2 = mlflow_context.client_dst
    import_all(client2, mlflow_context.output_dir, delete_model=False)
    exps2 = client2.search_experiments()
    runs2 = client2.search_runs([exp.experiment_id for exp in exps2])
    return len(runs2)


def test_export_all_experiment_runs(mlflow_context):
    """ 
    Test that we export all runs of experiments that are referenced by version runs.
    """
    num_runs = _run_test_export_runs(mlflow_context, True)
    assert num_runs == _num_runs1 + _num_runs2


def test_export_only_version_runs(mlflow_context):
    """ 
    Test that we export only runs referenced by version.
    """
    num_runs = _run_test_export_runs(mlflow_context, False)
    assert num_runs == 2


# == Pparsing tests for extracting model names from CLI comma-delimitd string option 

def test_get_model_names_from_comma_delimited_string(mlflow_context):
    delete_experiments_and_models(mlflow_context)
    model_names = bulk_utils.get_model_names(mlflow_context.client_src,"model1,model2,model3")
    assert len(model_names) == 3


def test_get_model_names_from_all_string(mlflow_context):
    delete_experiments_and_models(mlflow_context)
    model_names1 = [ create_model(mlflow_context.client_src) for j in range(0,3) ]
    model_names2 = bulk_utils.get_model_names(mlflow_context.client_src, "*")
    assert set(model_names1) == set(model_names2)
