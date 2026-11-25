# IR: {"sets":{"T":"range(num_tasks)","N":"range(num_nodes)","C":"range(num_conflict_pairs)"},"params":{"num_tasks":"params['num_tasks']","num_nodes":"params['num_nodes']","num_conflict_pairs":"params['num_conflict_pairs']","conflict_pairs":"params['conflict_pairs']","allowable_nodes":"params['allowable_nodes']"},"variables":{"x[t,n]":"binary; upper bound 1 if n in allowable_nodes[t], otherwise 0","peak":"nonnegative integer"},"constraints":["For each t in T: sum(x[t,n] for n in N) = 1.","For each c in C and n in N, with (a,b)=conflict_pairs[c]: x[a,n]+x[b,n] <= 1.","For each t in T and n in N: n*x[t,n] <= peak."],"objective":"minimize peak"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_tasks = params["num_tasks"]
    num_nodes = params["num_nodes"]
    num_conflict_pairs = params["num_conflict_pairs"]
    conflict_pairs = params["conflict_pairs"]
    allowable_nodes = params["allowable_nodes"]

    allowed = [set(allowable_nodes[task]) for task in range(num_tasks)]

    model = pyo.ConcreteModel()
    model.tasks = pyo.Set(initialize=range(num_tasks), ordered=True)
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.conflicts = pyo.Set(
        initialize=range(num_conflict_pairs), ordered=True
    )

    def assignment_bounds(instance, task, node):
        return (0, 1 if node in allowed[task] else 0)

    model.assignment = pyo.Var(
        model.tasks,
        model.nodes,
        domain=pyo.Binary,
        bounds=assignment_bounds,
    )
    model.peak = pyo.Var(domain=pyo.NonNegativeIntegers)

    def assign_once_rule(instance, task):
        if num_nodes == 0:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            instance.assignment[task, node] for node in instance.nodes
        ) == 1

    model.assign_once = pyo.Constraint(
        model.tasks, rule=assign_once_rule
    )

    def conflict_rule(instance, pair_index, node):
        first_task, second_task = conflict_pairs[pair_index]
        return (
            instance.assignment[first_task, node]
            + instance.assignment[second_task, node]
            <= 1
        )

    model.conflict_limits = pyo.Constraint(
        model.conflicts, model.nodes, rule=conflict_rule
    )

    def peak_rule(instance, task, node):
        return node * instance.assignment[task, node] <= instance.peak

    model.peak_limits = pyo.Constraint(
        model.tasks, model.nodes, rule=peak_rule
    )
    model.objective = pyo.Objective(
        expr=model.peak, sense=pyo.minimize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}