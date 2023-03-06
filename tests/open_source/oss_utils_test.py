import shortuuid
import mlflow
##import mlflow.sklearn
import sklearn_utils
from mlflow_export_import.common import model_utils
from mlflow.utils.mlflow_tags import MLFLOW_RUN_NOTE # NOTE: ""mlflow.note.content" - used for Experiment Description too!
from init_tests import mlflow_context
import utils_test

print("MLflow version:", mlflow.__version__)

def init_output_dirs(output_dir):
    utils_test.create_output_dir(output_dir)
    return utils_test.create_run_artifact_dirs(output_dir)


def mk_uuid():
    return shortuuid.uuid()

TEST_OBJECT_PREFIX = "test_exim" 

def mk_test_object_name_default():
    return f"{TEST_OBJECT_PREFIX}_{mk_uuid()}"

    
def create_experiment(client, mk_test_object_name=mk_test_object_name_default):
    exp_name = f"{mk_test_object_name()}"
    mlflow.set_experiment(exp_name)
    exp = client.get_experiment_by_name(exp_name)
    client.set_experiment_tag(exp.experiment_id, "version_mlflow", mlflow.__version__)
    client.set_experiment_tag(exp.experiment_id, MLFLOW_RUN_NOTE, f"Description_{mk_uuid()}")
    exp = client.get_experiment(exp.experiment_id)
    for info in client.search_runs(exp.experiment_id):
        client.delete_run(info.run_id)
    return exp


def create_simple_run(client, run_name=None, use_metric_steps=False):
    exp = create_experiment(client)
    max_depth = 4
    model = sklearn_utils.create_sklearn_model(max_depth)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_param("max_depth",max_depth)
        if use_metric_steps:
            for j in range(0,5):
                mlflow.log_metric("rmse",.789+j,j)
        else:
            mlflow.log_metric("rmse", 0.789)
        mlflow.set_tag("my_tag", "my_val")
        mlflow.set_tag("my_uuid",mk_uuid())
        mlflow.sklearn.log_model(model, "model")
        with open("info.txt", "w", encoding="utf-8") as f:
            f.write("Hi artifact")
        mlflow.log_artifact("info.txt")
        mlflow.log_artifact("info.txt", "dir2")
        mlflow.log_metric("m1", 0.1)
    run = client.get_run(run.info.run_id)
    return exp, run


def create_runs(client):
    create_experiment()
    with mlflow.start_run() as run:
        mlflow.log_param("p1", "hi")
        mlflow.log_metric("m1", 0.786)
        mlflow.set_tag("t1", "hi")
    return client.search_runs(run.info.experiment_id, "")


def list_experiments(client):
    return [ exp for exp in client.search_experiments() if exp.name.startswith(TEST_OBJECT_PREFIX) ]


def delete_experiment(client, exp):
    client.delete_experiment(exp.experiment_id)


def delete_experiments(client):
    for exp in client.search_experiments():
        client.delete_experiment(exp.experiment_id)


def delete_models(client):
    for model in client.search_registered_models(max_results=1000):
        model_utils.delete_model(client, model.name)


def delete_experiments_and_models(mlflow_context):
    delete_experiments(mlflow_context.client_src)
    delete_experiments(mlflow_context.client_dst)
    delete_models(mlflow_context.client_src)
    delete_models(mlflow_context.client_dst)
    utils_test.create_output_dir(mlflow_context.output_dir)


def dump_tags(tags, msg=""):
    print(f"==== {len(tags)} Tags:",msg)
    tags = dict(sorted(tags.items()))
    for k,v in tags.items():
        print(f"  {k}: {v}")


def create_dst_experiment_name(experiment_name):
    # NOTE: OK as is if running two tracking servers. If running on one tracking server, will need to adjust by adding random prefix."
    return experiment_name


def create_dst_model_name(model_name):
    return model_name
