import os
import mlflow
from mlflow_export_import.bulk import bulk_utils
from oss_utils_test import create_experiment, mk_uuid, delete_experiments_and_models, mk_test_object_name_default
import sklearn_utils
from compare_utils import compare_runs
from mlflow_export_import.bulk.export_experiments import export_experiments
from mlflow_export_import.bulk.import_experiments import import_experiments
from init_tests import mlflow_context

notebook_formats = "SOURCE,DBC"

# == Setup

mlmodel_fix = True

def _create_simple_run(idx=0):
    model = sklearn_utils.create_sklearn_model(max_depth=4)
    with mlflow.start_run(run_name=f"run_{idx}"):
        mlflow.log_param("run_index", idx)
        mlflow.log_metric("rmse", 0.789+idx)
        mlflow.set_tag("my_uuid" ,mk_uuid())
        mlflow.set_tag("run_index", idx)
        mlflow.sklearn.log_model(model, "model")
        with open("info.txt", "wt", encoding="utf-8") as f:
            f.write("Hi artifact")
        mlflow.log_artifact("info.txt")
        mlflow.log_artifact("info.txt", "dir2")
        mlflow.log_metric("m1", idx)


def create_test_experiment(client, num_runs, mk_test_object_name=mk_test_object_name_default):
    exp = create_experiment(client, mk_test_object_name)
    for j in range(num_runs):
        _create_simple_run(j)
    return exp


# == Compare

def compare_experiments(mlflow_context, compare_func):
    exps1 = sorted(mlflow_context.client_src.search_experiments(), key=lambda x: x.name)
    exps2 = sorted(mlflow_context.client_dst.search_experiments(), key=lambda x: x.name)
    assert len(exps1) == len(exps2)
    for x in zip(exps1, exps2):
        exp1, exp2 = x[0], x[1]
        assert exp1.name == exp2.name
        runs1 = mlflow_context.client_src.search_runs(exp1.experiment_id)
        runs2 = mlflow_context.client_dst.search_runs(exp2.experiment_id)
        assert len(runs1) == len(runs2)
    for run1 in mlflow_context.client_src.search_runs(exp1.experiment_id, ""):
        tag = run1.data.tags["run_index"]
        run2 = mlflow_context.client_dst.search_runs(exp2.experiment_id, f"tags.run_index = '{tag}'")[0]
        #assert run1.data.tags["tags.run_index] = run2.data.tags["tags.run_index]
        base_dir = os.path.join(mlflow_context.output_dir,"test_compare_runs")
        os.makedirs(base_dir, exist_ok=True)
        odir = os.path.join(base_dir,run1.info.experiment_id)
        compare_func(mlflow_context.client_src, mlflow_context.client_dst, run1, run2, odir)

# == Export/import Experiments tests

def _run_test(mlflow_context, compare_func, use_threads=False):
    delete_experiments_and_models(mlflow_context)
    exps = [ create_test_experiment(mlflow_context.client_src, 3), create_test_experiment(mlflow_context.client_src, 4) ]
    exp_names = [ exp.name for exp in exps ]
    export_experiments(mlflow_context.client_src,
        experiments = exp_names,
        output_dir = mlflow_context.output_dir,
        notebook_formats = notebook_formats,
        use_threads = use_threads)

    import_experiments(mlflow_context.client_dst, mlflow_context.output_dir, use_src_user_id=False, use_threads=False)
    compare_experiments(mlflow_context, compare_func)


def test_exp_basic(mlflow_context):
    _run_test(mlflow_context, compare_runs)


def test_exp_basic_threads(mlflow_context):
    _run_test(mlflow_context, compare_runs, use_threads=True)


#def test_exp_with_source_tags(mlflow_context): # TODO
    #_run_test(mlflow_context, compare_runs)


def test_get_experiment_ids_from_comma_delimited_string(mlflow_context):
    exp_ids = bulk_utils.get_experiment_ids(mlflow_context.client_src, "exp1,exp2,exp3")
    assert len(exp_ids) == 3


def test_get_experiment_ids_from_all_string(mlflow_context):
    delete_experiments_and_models(mlflow_context)
    exps = [ create_test_experiment(mlflow_context.client_src, 3), create_test_experiment(mlflow_context.client_src, 4) ]
    exp_ids = bulk_utils.get_experiment_ids(mlflow_context.client_src, "all")
    assert sorted(exp_ids) == sorted([exp.experiment_id for exp in exps])


def test_get_experiment_ids_from_list(mlflow_context):
    exp_ids1 = ["exp1","exp2","exp3"]
    exp_ids2 = bulk_utils.get_experiment_ids(mlflow_context.client_src, exp_ids1)
    assert exp_ids1 == exp_ids2
