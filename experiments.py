import instance
from logger import Logger
import solvers
from PathTable import PathTable
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np



def run_scenario(map_path, agent_path, solver, log_file = 'experiments.csv', verbose = True, n_paths = 2, temp = 1):
    inst = instance.instance(map_path, agent_path, solver, verbose, n_paths, agent_path_temp = temp)
    logger = Logger(log_file, inst)
    t = PathTable(inst.num_of_rows, inst.num_of_cols)
    solver = solvers.RandomPP(inst, t)
    logger.start()
    solver.solve()
    n_solved = solver.n_solved
    logger.end()
    logger.log(n_solved)

def run_all_scenarios(map_name, agent_directory, solver, verbose = True, n_paths = 2):
    for agent_name in os.listdir(agent_directory):
        agent_path = os.path.join(agent_directory, agent_name)
        print(agent_path)
        run_scenario(map_name, agent_path, solver, verbose = True, n_paths = 2)


def temp_ablation(map_path, agent_path, solver, verbose = True, n_paths = 2, temp = 1):
    open('temp_ablation.csv', "a")
    temps = np.logspace(-2, 0, 100)
    #temps = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.8, 1, 1.1, 1.2 , 1.3 , 1.5]
    for temp in temps:
        run_scenario(map_path, agent_path, solver,'temp_ablation.csv', verbose, n_paths, temp)


def pandas_exp():
    df = pd.read_csv('n_path_ablation.csv')
    #df = df[['percent_solved', 'agent_temp']]
    df.plot(x = 'n_paths', y = 'percent_solved')
    plt.show()
    #print(df.to_string())
    #print(df['percent_solved'].to_string())

def n_path_ablation(map_path, agent_path, solver, verbose = True, temp = 1):
    open('n_path_ablation.csv', "a")
    n_paths = range(1,33)
    #temps = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.8, 1, 1.1, 1.2 , 1.3 , 1.5]
    for n_path in n_paths:
        run_scenario(map_path, agent_path, solver,'n_path_ablation.csv', verbose, n_path, temp)
