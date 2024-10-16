import json
import logging
import os
import shutil
from datetime import datetime
from typing import Optional

import pandas as pd

from autorag.data.chunk.run import run_chunker
from autorag.data.utils.util import load_yaml, get_param_combinations

logger = logging.getLogger("AutoRAG")


class Chunker:
	def __init__(self, raw_df: pd.DataFrame, project_dir: Optional[str] = None):
		self.parsed_raw = raw_df
		self.project_dir = project_dir if project_dir is not None else os.getcwd()

	@classmethod
	def from_parquet(
		cls, parsed_data_path: str, project_dir: Optional[str] = None
	) -> "Chunker":
		if not os.path.exists(parsed_data_path):
			raise ValueError(f"parsed_data_path {parsed_data_path} does not exist.")
		if not parsed_data_path.endswith("parquet"):
			raise ValueError(
				f"parsed_data_path {parsed_data_path} is not a parquet file."
			)
		parsed_result = pd.read_parquet(parsed_data_path, engine="pyarrow")
		return cls(parsed_result, project_dir)

	def start_chunking(self, yaml_path: str):
		trial_name = self.__get_new_trial_name()
		self.__make_trial_dir(trial_name)

		# Copy YAML file to the trial directory
		shutil.copy(
			yaml_path, os.path.join(self.project_dir, trial_name, "chunk_config.yaml")
		)

		# load yaml file
		modules = load_yaml(yaml_path)

		input_modules, input_params = get_param_combinations(modules)

		logger.info("Chunking Start...")
		run_chunker(
			modules=input_modules,
			module_params=input_params,
			parsed_result=self.parsed_raw,
			trial_path=os.path.join(self.project_dir, trial_name),
		)
		logger.info("Chunking Done!")

	def __get_new_trial_name(self) -> str:
		trial_json_path = os.path.join(self.project_dir, "trial.json")
		if not os.path.exists(trial_json_path):
			return "0"
		with open(trial_json_path, "r") as f:
			trial_json = json.load(f)
		return str(int(trial_json[-1]["trial_name"]) + 1)

	def __make_trial_dir(self, trial_name: str):
		trial_json_path = os.path.join(self.project_dir, "trial.json")
		if os.path.exists(trial_json_path):
			with open(trial_json_path, "r") as f:
				trial_json = json.load(f)
		else:
			trial_json = []

		trial_json.append(
			{
				"trial_name": trial_name,
				"start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			}
		)
		os.makedirs(os.path.join(self.project_dir, trial_name))
		with open(trial_json_path, "w") as f:
			json.dump(trial_json, f, indent=4)