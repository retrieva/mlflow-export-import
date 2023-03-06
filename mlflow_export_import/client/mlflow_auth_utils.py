from mlflow_export_import.client import databricks_cli_utils
from mlflow_export_import.common import MlflowExportImportException

def get_mlflow_host():
    """ Returns the MLflow tracking URI (host) """
    return get_mlflow_host_token()[0]


def get_mlflow_host_token():
    """ Returns the MLflow tracking URI (host) and Databricks personal access token (PAT)"""

    import mlflow
    uri = mlflow.tracking.get_tracking_uri()
    #uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if uri:
        if not uri.startswith("databricks"):
            if not uri.startswith("http"):
                _raise_exception(uri)
            else:
                return (uri, None)
    else:
        _raise_exception(uri)

    try:
        toks = uri.split("//")
        profile = uri.split("//")[1] if len(toks) > 1 else None
        return databricks_cli_utils.get_host_token(profile)
    # databricks_cli.utils.InvalidConfigurationError 
    # requests.exceptions.InvalidSchema(f"No connection adapters were found for {url!r}")
    except Exception as e: 
        print("WARNING:", e)
        return (None, None)


def _raise_exception(uri):
    raise MlflowExportImportException(
      f"MLflow tracking URI (MLFLOW_TRACKING_URI environment variable) must be an HTTP URI: '{uri}'.",
      http_status_code=401)
