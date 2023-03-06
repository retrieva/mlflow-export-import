# Databricks notebook source
# MAGIC %md ## MLflow Export Import - Single Notebooks
# MAGIC 
# MAGIC Copy one MLflow object and control its destination object name.
# MAGIC 
# MAGIC **Notebooks**
# MAGIC * Run
# MAGIC   * [Export_Run]($./Export_Run)  
# MAGIC   * [Import_Run]($./Import_Run)
# MAGIC * Experiment
# MAGIC   * [Export_Experiment]($./Export_Experiment) - export an experiment and all its runs (run.info, run.data and artifacts).
# MAGIC   * [Import_Experiment]($./Import_Experiment)
# MAGIC * Registered Model
# MAGIC   * [Export_Model]($./Export_Model) - export a model, its versions and the version's run.
# MAGIC   * [Import_Model]($./Import_Model)
# MAGIC * [Common]($./Common)
# MAGIC 
# MAGIC Core code: https://github.com/mlflow/mlflow-export-import/blob/master/README_single.md.

# COMMAND ----------

# MAGIC %md Last updated: 2023-01-19