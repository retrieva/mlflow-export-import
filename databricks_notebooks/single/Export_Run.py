# Databricks notebook source
# MAGIC %md ### Export Run
# MAGIC 
# MAGIC ##### Overview
# MAGIC * Exports an run and its artifacts to a folder.
# MAGIC * Output file `run.json` contains top-level run metadata.
# MAGIC * Notebooks are also exported in several formats.
# MAGIC 
# MAGIC #### Output folder
# MAGIC ```
# MAGIC 
# MAGIC +-artifacts/
# MAGIC | +-plot.png
# MAGIC | +-sklearn-model/
# MAGIC | | +-model.pkl
# MAGIC | | +-conda.yaml
# MAGIC | |
# MAGIC +-run.json
# MAGIC ```
# MAGIC 
# MAGIC ##### Widgets
# MAGIC * Run ID 
# MAGIC * Output base directory - Base output folder of the exported run.
# MAGIC * Notebook formats:
# MAGIC   * Standard Databricks notebook formats such as SOURCE, HTML, JUPYTER, DBC. 
# MAGIC   * See [Databricks Export Format](https://docs.databricks.com/dev-tools/api/latest/workspace.html#notebookexportformat)  documentation.
# MAGIC   
# MAGIC #### Setup
# MAGIC * See Setup in [README]($./_README).

# COMMAND ----------

# MAGIC %run ./Common

# COMMAND ----------

# MAGIC %md ### Setup

# COMMAND ----------

dbutils.widgets.text("1. Run ID", "") 
run_id = dbutils.widgets.get("1. Run ID")

dbutils.widgets.text("2. Output base directory", "") 
output_dir = dbutils.widgets.get("2. Output base directory")
output_dir += f"/{run_id}"

notebook_formats = get_notebook_formats(3)

print("run_id:", run_id)
print("output_dir:", output_dir)
print("notebook_formats:", notebook_formats)

# COMMAND ----------

assert_widget(run_id, "1. Run ID")
assert_widget(output_dir, "2. Output base directory")
  
import mlflow

# COMMAND ----------

# MAGIC %md ### Display MLflow UI URI of Run

# COMMAND ----------

display_run_uri(run_id)

# COMMAND ----------

# MAGIC %md ### Remove any previous exported run data

# COMMAND ----------

dbutils.fs.rm(output_dir, True)

# COMMAND ----------

# MAGIC %md ### Export the run

# COMMAND ----------

from mlflow_export_import.run.export_run import RunExporter
exporter = RunExporter(mlflow.client.MlflowClient(), 
                       notebook_formats=notebook_formats)
exporter.export_run(run_id, output_dir)

# COMMAND ----------

# MAGIC %md ### Display  exported run files

# COMMAND ----------

import os
output_dir = output_dir.replace("dbfs:","/dbfs")
os.environ['OUTPUT_DIR'] = output_dir

# COMMAND ----------

# MAGIC %sh echo $OUTPUT_DIR

# COMMAND ----------

# MAGIC %sh ls -l $OUTPUT_DIR

# COMMAND ----------

# MAGIC %sh cat $OUTPUT_DIR/run.json

# COMMAND ----------

# MAGIC %sh ls -lR $OUTPUT_DIR/artifacts