import sys

import torch

from utils.timer import Timer
import utils.pseudo_random as pseudo_random
import utils.output as output
from settings.constants import OpponentType

"""Section Data Management and Paths"""
# the directory for data files
data_directory = '../data/'
# folders for data per street
street_folders = {0: "preflop-aux", 1: "preflop/", 2: "flop/", 3: "turn/", 4: "river/"}
# names of streets for printing
street_names = {1: "Pre-flop", 2: "Flop", 3: "Turn", 4: "River"}
# path to the solved poker situation data used to train the neural net
training_data_path = '../../data/training_samples/'
# path to the models during training
training_model_path = '../../data/models/'
# folder for raw training files
training_data_raw = 'raw/'
# folder for converted / bucketed training files
training_data_converted = 'bucketed/'
# file patter for input files
inputs_extension = ".inputs"
# file extension for targets files
targets_extension = ".targets"
# path to the neural net models
model_path = '../data/models/'
# the name of a neural net file
value_net_name = 'final'
# the extension of a neural net file
value_net_extension = '.tar'
# flag whether to use sqlite database for bucketing information (otherwise use data files)
use_sqlite = False

"""Section CFR Iterations"""
# the number of iterations that DyypHoldem runs CFR for
cfr_iters = 1000
# the number of preliminary CFR iterations which DyypHoldem doesn't factor into the average strategy (included in cfr_iters)
cfr_skip_iters = 500

"""Section Data Generation"""
# how many poker situations are solved simultaneously during data generation
gen_batch_size = 10
# how many solved poker situations are generated for use as training examples
gen_data_count = 100000

"""Section Training"""
# how many poker situations are used in each neural net training batch - has to be a multiple of gen_batch_size !
train_batch_size = 1000
# how many epochs to train for
epoch_count = 200
# how often to save the model during training
save_epoch = 10
# automatically save the best epoch as final model
save_best_epoch = True
# learning rate for neural net training
learning_rate = 0.001
# resume training if a final model already exists
resume_training = False

"""Section Torch"""
# flag to use GPU for calculations
use_gpu = False
# default tensor types
if not use_gpu:
    Tensor = torch.FloatTensor
    LongTensor = torch.LongTensor
    value_net_name = value_net_name + "_cpu"
else:
    Tensor = torch.cuda.FloatTensor
    LongTensor = torch.cuda.LongTensor
    value_net_name = value_net_name + "_gpu"
    # flag to use new tensor cores on Ampere based GPUs - set to 'False' for reproducibility
    torch.backends.cuda.matmul.allow_tf32 = False
# device name for torch
device = torch.device('cpu') if not use_gpu else torch.device('cuda')

"""Section Random"""
# flag to choose between official or internal random number generator - set to 'True' for reproducibility
use_pseudo_random = False
if use_pseudo_random:
    pseudo_random.manual_seed(123)

"""Section Global Objects"""
# global logger
use_loguru = True
if use_loguru:
    import loguru

    logger = loguru.logger
    logger.remove(0)
    logger.level("LOADING", no=8, color="<fg #944100><bold>", icon="@")
    logger.level("TIMING", no=15, color="<fg #b88210><bold>", icon="@")
    logger.level("TRACE", color="<fg #717171><bold>")
    log_format_stderr = "| <level>{level: <8}</level> | <level>{message}</level>"
    log_format_file = "{time:YYYY-MM-DD HH:mm:ss.SS} | {level: <8} | {message}"
    logging_level_stderr = "TRACE"
    logging_level_file = "TRACE"
    logger.add(sys.stderr, format=log_format_stderr, level=logging_level_stderr)
    logger.add("../logs/dyypholdem.log", format=log_format_file, level=logging_level_file, rotation="10 MB")
else:
    logger = output.DummyLogger("TRACE")

# a global timer used to measure loading and calculation times
"""Section slumbot connection"""
slumbot_username = "your_username"
slumbot_password = "your_password"

"""CDBR Section"""
cdbr = False
cdbr_type = OpponentType.always_call
cdbr_new_initialization = True
cdbr_only_fold_call_rounds = None
cdbr_strategy_path = "C:/Programy/dyypholdem/data/strategy{}.pkl"
cdbr_ready_path = "C:/Programy/dyypholdem/data/ready{}.txt"

"""Section analysis"""
results_path = "G:/My Drive/Doktorat/BigExperimentLogs/DyypHoldem"
results_folder = ["LBR vs Slumbot", "CDBR vs Slumbot", "LBR(fc12) vs Slumbot", "LBR(c12) vs Slumbot", "CDBR(fc12) vs Slumbot"]
# results_folder = ["DS vs Uniform", "CDBR vs Uniform", "LBR vs Uniform", "LBR(f) vs Uniform", "CDBR(fc12) vs Uniform", "LBR(fc12) vs Uniform", "LBR vs CallRaise", "LBR(fc12) vs CallRaise"]

t_test_folders = ["CDBR vs SlumBot", "LBR vs SlumBot"]

"""Section prints"""
print_strategy = False

timer = Timer(logger)

logger.info("Environment setup complete - initializing...")
