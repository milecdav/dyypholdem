import settings.arguments as arguments
import utils.stats as my_stats

if __name__ == '__main__':
    for last_folder_name in arguments.results_folder:
        folder_name = arguments.results_path + "/" + last_folder_name
        interval, mean = my_stats.compute_confidence_interval(my_stats.open_all_files_and_combine_data(folder_name))
        arguments.logger.success(f"Computed the statistics for {last_folder_name}, mean: {mean} ± {interval[1] - mean}")
