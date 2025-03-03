import PathTable
import instance
import PathTable
import numpy as np
from LowLevelSolvers import PPNeighborhoodRepair, ExhaustiveNeighborhoodRepair, RankPPNeighborhoodRepair, NeighborhoodRepair, CBSNeighborhoodRepair
import DestroyMethods
import copy
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import typing

def random_initial_solution(instance: instance.instance, path_table: PathTable.PathTable):
    random_path_selection = np.random.randint(instance.n_paths, size=instance.num_agents)
    for agent_id, path_idx in zip(instance.agents.keys(), random_path_selection):
        path_table.insert_path(agent_id, instance.agents[agent_id].paths[path_idx])
        instance.agents[agent_id].path_id = int(path_idx)
    path_table.calculate_makespan()

def generate_random_random_solution_iterative(instance: instance.instance, path_table: PathTable.PathTable, iterations = 200, low_level_solver_name = 'pp'):
    random_initial_solution(instance, path_table) # Choose random paths as initial solution
    solver = IterativeRandomLNS(instance, path_table, 3, num_iterations = iterations, low_level_solver_name=low_level_solver_name)
    return solver.run()
class RandomPP:
    def __init__(self, instance: instance.instance, path_table:PathTable.PathTable):
        self.instance = instance
        self.path_table = path_table
        self.n_solved = 0
        self.verbose = self.instance.verbose
    def solve_for_agent(self, agent_id, agent):
        for i in range(len(agent.paths)):
            if self.path_table.is_path_available(agent.paths[i]):
                self.path_table.insert_path(agent_id, agent.paths[i])
                agent.path_id = i
                self.n_solved += 1
                return True
        return False
    def solve(self):
        if self.verbose:
            print(f'\n**** Using Random PP Solver on {self.instance.instance_name}: ****')

        for agent_id, agent in self.instance.agents.items():
            self.solve_for_agent(agent_id, agent)

        if self.verbose:
            print(f'\n**** Successfully solved for {self.n_solved} agents: ****')
            print(f'\n     Failed for {self.instance.num_agents - self.n_solved} agents\n')


class IterativeRandomLNS:
    def __init__(self, instance: instance.instance, path_table:PathTable.PathTable, subset_size, num_iterations = 1000, destroy_method_name = 'priority', low_level_solver_name = 'pp', random_seed: int = None):
        self.instance = instance
        self.path_table = path_table
        self.subset_size = subset_size
        self.verbose = self.instance.verbose
        self.num_iterations = num_iterations
        self.num_collisions = self.path_table.num_collisions(self.instance.num_agents)
        self.collision_statistics = [self.num_collisions]
        destroy_methods = {'random': DestroyMethods.RandomDestroyHeuristic,
                           'w-random': DestroyMethods.RandomWeightedDestroyHeuristic,
                           'priority': DestroyMethods.PriorityDestroyHeuristic,
                           'cc': DestroyMethods.ConnectedComponentDestroyHeuristic}
        dm = destroy_methods[destroy_method_name]
        self.destroy_heuristic = dm(instance, path_table, subset_size)

        solvers_list = {'pp': PPNeighborhoodRepair,
                        'rank-pp': RankPPNeighborhoodRepair,
                        'exhaustive': ExhaustiveNeighborhoodRepair,
                        'cbs': CBSNeighborhoodRepair}
        self.low_level_solver = solvers_list[low_level_solver_name]
        self.random_seed = random_seed



    def run_iteration(self):
        subset = self.destroy_heuristic.generate_subset()#np.random.choice(range(1, self.instance.num_agents+1), self.subset_size, replace=False)
        if self.verbose:
            print(subset)
        subset_path_ids = [int(self.instance.agents[agent_id].path_id) for agent_id in subset]
        if self.verbose:
            print(subset_path_ids)
            print(f'\n**** Initial number of collisions: {self.num_collisions} ****')
        low_level_solver = self.low_level_solver(agent_cost_type = 'mean', instance = self.instance,path_table =  self.path_table, agent_subset = subset, verbose=False)
        low_level_solver.run()
        new_num_collisions = self.path_table.num_collisions(self.instance.num_agents)
        if new_num_collisions < self.num_collisions:
            self.num_collisions = new_num_collisions
            if self.verbose:
                print(f'**** Iteration successful! ****')
                print(f'        New path ids: {[int(self.instance.agents[agent_id].path_id) for agent_id in subset]} ****')
                print(f'        New collision count: {self.num_collisions} ****\n')
        else:
            low_level_solver.destroy_neighborhood()
            for agent_id, path_id in zip(subset, subset_path_ids):
                agent = self.instance.agents[agent_id]
                agent.path_id = path_id
                self.path_table.insert_path(agent_id, agent.paths[path_id])
            if self.verbose:
                print(f'**** Iteration failed! \n****')
        self.collision_statistics += [self.num_collisions]


    def run(self, early_stopping = False):
        # used for determinism in parallelization tests
        if self.random_seed is not None:
            np.random.seed(self.random_seed)

        for iteration in range(self.num_iterations):
            prev_collisions = self.num_collisions
            self.run_iteration()
            if early_stopping and (self.num_collisions < prev_collisions):
                return self, iteration + 1

        return self, self.num_iterations

