import settings.arguments as arguments
import utils.stats as my_stats

if __name__ == '__main__':
    all_data = [my_stats.open_all_files_and_combine_data(arguments.results_path + "/" + directory) for directory in arguments.t_test_folders]
    interval, mean = my_stats.compute_confidence_interval(all_data[0])
    arguments.logger.success(f"Computed the statistics for {arguments.t_test_folders[0]}, mean: {mean} ± {interval[1] - mean}")
    interval, mean = my_stats.compute_confidence_interval(all_data[1])
    arguments.logger.success(f"Computed the statistics for {arguments.t_test_folders[1]}, mean: {mean} ± {interval[1] - mean}")
    stat, p = my_stats.t_test(all_data)
    arguments.logger.success(f"Computed the statistics: {stat} with p value {p}")
