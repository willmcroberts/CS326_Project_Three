import time
import json
import os

class CSP:
    def __init__(self, variables, domains, neighbors, constraints):
        self.variables = variables
        self.domains = {v: list(domains[v]) for v in variables}
        self.neighbors = neighbors
        self.constraints = constraints
        self.assignments = 0
        self.backtracks = 0

    def is_consistent(self, var, value, assignment):
        for n in self.neighbors[var]:
            if n in assignment:
                if not self.constraints(var, value, n, assignment[n]):
                    return False
        return True

    def select_unassigned_variable(self, assignment):
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: len(self.domains[v]))

    def order_domain_values(self, var, assignment, use_lcv):
        if not use_lcv:
            return list(self.domains[var])

        def conflicts(value):
            count = 0
            for n in self.neighbors[var]:
                if n not in assignment:
                    for v in self.domains[n]:
                        if not self.constraints(var, value, n, v):
                            count += 1
            return count

        return sorted(self.domains[var], key=conflicts)

    def forward_check(self, var, value, assignment):
        removed = []
        for n in self.neighbors[var]:
            if n not in assignment:
                for v in list(self.domains[n]):
                    if not self.constraints(var, value, n, v):
                        self.domains[n].remove(v)
                        removed.append((n, v))
                if not self.domains[n]:
                    return False, removed
        return True, removed

    def backtrack(self, assignment, use_fc, use_lcv):
        if len(assignment) == len(self.variables):
            return assignment

        var = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(var, assignment, use_lcv):
            if self.is_consistent(var, value, assignment):
                assignment[var] = value
                self.assignments += 1

                if use_fc:
                    ok, removed = self.forward_check(var, value, assignment)
                    if ok:
                        back_track_result = self.backtrack(assignment, use_fc, use_lcv)
                        if back_track_result is not None:
                            return back_track_result
                    for (n, v) in removed:
                        self.domains[n].append(v)
                else:
                    back_track_result = self.backtrack(assignment, use_fc, use_lcv)
                    if back_track_result is not None:
                        return back_track_result

                del assignment[var]
                self.backtracks += 1

        return None

    def solve(self, configure):
        use_fc = ("fc" in configure)
        use_lcv = ("lcv" in configure)

        start = time.time()
        assignment = {}
        backtrack_assignment = self.backtrack(assignment, use_fc, use_lcv)
        end = time.time()

        return {
            "solved": backtrack_assignment is not None,
            "solution": backtrack_assignment,
            "runtime_ms": round((end - start) * 1000, 3),
            "assignments": self.assignments,
            "backtracks": self.backtracks
        }

def sudoku_neighbors():
    neighbors = {}
    for r in range(9):
        for c in range(9):
            v = (r, c)
            neighbors[v] = set()
            for cc in range(9):
                if cc != c:
                    neighbors[v].add((r, cc))
            for rr in range(9):
                if rr != r:
                    neighbors[v].add((rr, c))
            br, bc = 3 * (r // 3), 3 * (c // 3)
            for rr in range(br, br + 3):
                for cc in range(bc, bc + 3):
                    if (rr, cc) != (r, c):
                        neighbors[v].add((rr, cc))
    return neighbors

def sudoku_constraint(var1, val1, var2, val2):
    # var1 and var2 need to be passed, but are not used here.
    return val1 != val2

def load_sudoku(path):
    with open(path) as naming_a_variable:
        puzzle = json.load(naming_a_variable)["puzzle"]

    variables = [(r, c) for r in range(9) for c in range(9)]
    domains = {}

    for r in range(9):
        for c in range(9):
            if puzzle[r][c] == 0:
                domains[(r, c)] = list(range(1, 10))
            else:
                domains[(r, c)] = [puzzle[r][c]]

    neighbors = sudoku_neighbors()

    return CSP(variables, domains, neighbors, sudoku_constraint)

def format_sudoku(solution):
    grid = [[0]*9 for _ in range(9)]
    for (r,c), v in solution.items():
        grid[r][c] = v
    return grid

def print_sudoku(grid):
    for r in range(9):
        if r % 3 == 0 and r != 0:
            print("-" * 21)
        row = ""
        for c in range(9):
            if c % 3 == 0 and c != 0:
                row += "| "
            row += str(grid[r][c]) + " "
        print(row)

def map_constraint(var1, val1, var2, val2):
    # var1 and var2 need to be passed, but are not used here.
    return val1 != val2

def load_map(path):
    with open(path) as naming_another_variable:
        data = json.load(naming_another_variable)

    variables = data["regions"]
    domains = {r: list(data["colors"]) for r in variables}

    neighbors = {r: set() for r in variables}
    for (a, b) in data["adjacent"]:
        neighbors[a].add(b)
        neighbors[b].add(a)

    return CSP(variables, domains, neighbors, map_constraint)

def run_solver(type_of_puzzle, json_file_input, configure, seed=None):
    if seed is not None:
        import random
        random.seed(seed)

    if type_of_puzzle == "sudoku":
        csp = load_sudoku(json_file_input)
    elif type_of_puzzle == "map":
        csp = load_map(json_file_input)
    else:
        raise ValueError("Unknown problem")

    solved_result = csp.solve(configure)

    if type_of_puzzle == "sudoku" and solved_result["solved"]:
        solved_result["solution"] = format_sudoku(solved_result["solution"])

    return solved_result


if __name__ == "__main__":
# ✨✨✨✨✨ This is how to change the inputs ✨✨✨✨✨
    problem = "sudoku" # "sudoku" for a sudoku puzzle. "map" for a map puzzle
    instance = "puzzles/sudoku1.json" # "puzzles/sudoku1.json" for the sudoku file, "puzzles/australia.json" for the map puzzle. Add other sudoku and maps as needed
    config = "mrv_fc" # This doesn't change
# ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨

    result = run_solver(problem, instance, config)

    print(json.dumps({
        "problem": problem,
        "instance": instance,
        "config": config,
    }, indent=2))

    if problem == "sudoku":
        print_sudoku(result["solution"])

    os.makedirs("results", exist_ok=True)
    outpath = f"results/{problem}_{os.path.basename(instance)}_{config}.json"
    with open(outpath, "w") as f:
        json.dump(result, f, indent=2)