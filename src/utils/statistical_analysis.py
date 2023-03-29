import scipy.stats
import scipy.stats as stats
import numpy as np
import glob
import settings.arguments as arguments


def compute_confidence_interval(data, confidence=0.95):
    arguments.logger.info(f"Sucessfully loaded results from {len(data)} hands")
    sample_mean = np.mean(data)
    return stats.t.interval(confidence=confidence, df=len(data) - 1, loc=sample_mean, scale=stats.sem(data)), sample_mean


def create_data_from_file_only_winnings(file_path):
    data = []
    with open(file_path, 'r') as f:
        current = 0
        for line in f:
            parts = line.split()
            data.append(int(parts[1]))
            assert int(parts[1]) == int(parts[2]) - current
            current = int(parts[2])
    return data


def open_all_files_and_combine_data(directory):
    data = []
    for file_name in glob.glob(directory + "/*"):
        data += create_data_from_file_only_winnings(file_name)
    return data


if __name__ == '__main__':
    folder_name = arguments.results_path + "/" + arguments.results_folder
    interval, mean = compute_confidence_interval(open_all_files_and_combine_data(folder_name))
    arguments.logger.success(f"Computed the statistics, mean: {mean} ± {interval[1] - mean}")
