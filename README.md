**AutoExperiment**

A simple framework for automatically conducting a series of computational experiments, optimizing configuration hyperparameters to select the best configuration for each experimental trial.

*Usage* 
* Configure the parameters in config.json
* Run AutoExperiment, specifying the output directory on the command line

*Results format*
AutoExperiment expects that the experiments output a .csv file of results, with a name specified in the config file's expected_result_file setting, in the experiment directory or in expected_result_subdir beneath it if that is set

