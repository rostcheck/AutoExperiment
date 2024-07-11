# Perform an automated series of experiments guided by the configuration
import json
import argparse
import os
import logging
# import random
import shutil
import pandas
from scipy.optimize import minimize_scalar


# Load config
def read_config(config_filename):
    with open(config_filename) as json_file:
        return json.load(json_file)


# Save config
def write_config(config_filename, config_obj):
    with open(config_filename, 'w') as json_file:
        return json.dump(config_obj, json_file, indent=4)


def log(message):
    logging.info(f"{message}")


def get_result(this_experiment_dir, result_subdir, expected_result_file):
    # Verify the result file exists
    result_file = os.path.join(this_experiment_dir, result_subdir, expected_result_file)
    if not os.path.exists(result_file):
        logging.error(f"Error, could not find result file {result_file}")
        exit(-1)

    # Read results file into dataframe
    df = pandas.read_csv(result_file, index_col=0)
    try:
        return -1 * df.loc[target_output_row][target_output_column]
    except KeyError:
        logging.error(f"Error, expected target row {target_output_row} and column {target_output_column} missing "
                      " in result file {result_file}")
        exit(-1)


def experiment_dir_path(experiment_path, vary_param, tune_value):
    tune_value_string = str(tune_value).replace('.', '_')
    path = os.path.join(experiment_path, str(vary_param))
    path += f"-{tune_value_string}"
    return path


def objective(tune_value: float) -> float:
    # Protect against negative or 0 task generation time setting
    if tune_value <= 0:
        return 0.1
    # Set up initial parameters
    tune_value_string = str(tune_value).replace('.', '_')
    config_file_name = f"{this_vary_param}-{tune_value_string}.json"
    logging.info(f"Experimenting for {this_vary_param} w/ tune value {tune_value}")
    this_experiment_dir = experiment_dir_path(experiment_path, this_vary_param, tune_value)
    if not os.path.exists(this_experiment_dir):
        os.mkdir(this_experiment_dir)
    this_experiment_config_path = os.path.join(this_experiment_dir, config_file_name)

    # Generate the config file from the experiment template
    new_template = dict(template_config)
    new_template[run_vary_param] = this_vary_param
    new_template[tune_param] = tune_value
    write_config(this_experiment_config_path, new_template)

    # Run the experiment
    logging.info(f'Running experiment for {run_vary_param} {this_vary_param} with {tune_param} {tune_value}')
    cmd = f"{config['experiment_script']} {this_experiment_dir}"
    logging.info(f'cmd: {cmd}')
    os.system(cmd)

    # Get the result and adapt search
    result = get_result(this_experiment_dir, config['expected_result_subdir'], config['expected_result_file'])
    logging.info(f"result for {run_vary_param} {this_vary_param}: {result}")
    return result


# Set up logging
logging.basicConfig(level=logging.INFO)

# Read configuration
parser = argparse.ArgumentParser(description='Run a series of computational experiments, varying parameters as '
                                             'specified by config file')
parser.add_argument('experiment_dir', help='Experiment directory (containing config file)')
args = parser.parse_args()
if os.path.exists(args.experiment_dir):
    shutil.rmtree(args.experiment_dir)
experiment_path = os.path.join(args.experiment_dir, "tuning")
# Create the experiment path directory and any needed parent directories
os.makedirs(experiment_path, exist_ok=True)
config = read_config('config.json')

# Find the parameters to vary
long_vary_param = [key for key, value in config.items() if '$vary:' in key.lower()]
vary_list = config[long_vary_param[0]]
run_vary_param = long_vary_param[0].replace('$vary:', "")
logging.info(f"Varying parameter {run_vary_param} over list {vary_list}")

# Find the tuning parameter
# tuner = [key for key, value in config.items() if '$tune' in value]
# tune_param = tuner[0]
tune_param = config['tune_parameter']
range_max = float(config['range_max'])
range_min = float(config['range_min'])
max_iter = int(config['max_iter'])
# long_tune_value = config[tune_param]
# starting_tune_value = float(long_tune_value.replace('$tune:', ""))
# logging.info(f"Tuning parameter {tune_param} starting with {starting_tune_value}")
template_config = read_config('experiment_template.json')
target_output_row = config['target_output_row']
target_output_column = config['target_output_column']

# Loop over the parameter to vary, conducting an experiment for each one
for this_vary_param in vary_list:
    # minimize the function
    result = minimize_scalar(objective, method='bounded', bounds=[range_min, range_max], options={'maxiter': max_iter})
    # result = minimize_scalar(objective, method='brent', bracket=(0.1, 4))
    # summarize the result
    best_tune_value, best_result = result['x'], result['fun']
    logging.info(f"Best result for {run_vary_param} using {best_tune_value} was: {best_result}")

    # Rename the directory for the best experiment
    best_experiment_dir = experiment_dir_path(experiment_path, this_vary_param, best_tune_value)
    target_dir = os.path.join(args.experiment_dir, f"{this_vary_param}")
    logging.info(f"About to rename {best_experiment_dir} to {target_dir}")
    os.rename(best_experiment_dir, target_dir)
    shutil.rmtree(experiment_path)
    os.makedirs(experiment_path, exist_ok=True)
print('Experiments completed.')
