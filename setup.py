from setuptools import setup, find_packages

CORE_REQUIREMENTS = [
    "mlflow>=1.28.0",
    "wheel"
]

TEST_REQUIREMENTS = [
    "pytest>=7.2.0",
    "pytest-html",
    "shortuuid"
]
  
setup(
    name="mlflow_export_import",
    version = "1.2.0",
    author = "Andre Mesarovic",
    description = "Copy MLflow objects (experiments, runs or registered models) to another tracking server",
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    url = "https://github.com/mlflow/mlflow-export-import",
    project_urls={
        "Bug Tracker": "https://github.com/mlflow/mlflow-export-import/issues",
        "Documentation": "https://github.com/mlflow/mlflow-export-import/blob/master/README.md", 
        "Source Code": "https://github.com/mlflow/mlflow-export-import/"
    },
    python_requires = ">=3.8",
    packages = find_packages(),
    zip_safe = False,
    install_requires = CORE_REQUIREMENTS + TEST_REQUIREMENTS,
    license = "Apache License 2.0",
    keywords = "mlflow ml ai",
    classifiers = [
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent"
    ],
    entry_points = {
        "console_scripts": [
            "export-all = mlflow_export_import.bulk.export_all:main",
            "import-all = mlflow_export_import.bulk.import_models:main",
            "export-models = mlflow_export_import.bulk.export_models:main",
            "import-models = mlflow_export_import.bulk.import_models:main",
            "export-run = mlflow_export_import.run.export_run:main",
            "import-run = mlflow_export_import.run.import_run:main",
            "export-experiment = mlflow_export_import.experiment.export_experiment:main",
            "import-experiment = mlflow_export_import.experiment.import_experiment:main",
            "export-experiments = mlflow_export_import.bulk.export_experiments:main",
            "import-experiments = mlflow_export_import.bulk.import_experiments:main",
            "export-model = mlflow_export_import.model.export_model:main",
            "export-model-list = mlflow_export_import.model.export_model_list:main",
            "import-model = mlflow_export_import.model.import_model:main",
            "list-models = mlflow_export_import.model.list_registered_models:main",
            "download-notebook = mlflow_export_import.notebook.download_notebook:main",
            "http-client = mlflow_export_import.client.http_client:main"
         ]
      }
)
