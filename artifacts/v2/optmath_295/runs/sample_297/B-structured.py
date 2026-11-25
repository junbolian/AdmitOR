# IR: {"sets":{"N":"{0,...,num_nodes-1}; num_nodes frozen at 4","A":"{(i,j) in N x N: i != j}"},"params":["dist_0_1","dist_0_2","dist_0_3","dist_1_0","dist_1_2","dist_1_3","dist_2_0","dist_2_1","dist_2_3","dist_3_0","dist_3_1","dist_3_2","bigM","num_selected","num_nodes"],"variables":{"Nodes[i]":"binary, i in N","PairSelection[i,j]":"binary, (i,j) in A","MinDistance":"nonnegative continuous"},"constraints":["sum(Nodes[i] for i in N) = num_selected","MinDistance <= dist[i,j] + bigM*(1-PairSelection[i,j]) for (i,j) in A","PairSelection[i,j] <= Nodes[i] for (i,j) in A","PairSelection[i,j] <= Nodes[j] for (i,j) in A","PairSelection[i,j] >= Nodes[i]+Nodes[j]-1 for (i,j) in A"],"objective":"maximize MinDistance"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    if num_nodes != 4:
        return {"objective": None, "status": "invalid_num_nodes"}

    distances = {
        (0, 1): params["dist_0_1"],
        (0, 2): params["dist_0_2"],
        (0, 3): params["dist_0_3"],
        (1, 0): params["dist_1_0"],
        (1, 2): params["dist_1_2"],
        (1, 3): params["dist_1_3"],
        (2, 0): params["dist_2_0"],
        (2, 1): params["dist_2_1"],
        (2, 3): params["dist_2_3"],
        (3, 0): params["dist_3_0"],
        (3, 1): params["dist_3_1"],
        (3, 2): params["dist_3_2"],
    }

    model = pyo.ConcreteModel()
    model.node_count = pyo.Param(
        initialize=num_nodes, within=pyo.PositiveIntegers
    )
    model.N = pyo.RangeSet(0, int(pyo.value(model.node_count)) - 1)
    model.A = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in model.N for j in model.N if i != j],
    )

    model.dist = pyo.Param(
        model.A, initialize=distances, within=pyo.Reals
    )
    model.big_m = pyo.Param(
        initialize=params["bigM"], within=pyo.NonNegativeReals
    )
    model.selection_target = pyo.Param(
        initialize=params["num_selected"], within=pyo.Reals
    )

    model.Nodes = pyo.Var(model.N, domain=pyo.Binary)
    model.PairSelection = pyo.Var(model.A, domain=pyo.Binary)
    model.MinDistance = pyo.Var(domain=pyo.NonNegativeReals)

    model.facility_count = pyo.Constraint(
        expr=sum(model.Nodes[i] for i in model.N)
        == model.selection_target
    )

    def distance_rule(instance, i, j):
        return instance.MinDistance <= (
            instance.dist[i, j]
            + instance.big_m * (1 - instance.PairSelection[i, j])
        )

    model.distance_limits = pyo.Constraint(
        model.A, rule=distance_rule
    )

    def pair_first_rule(instance, i, j):
        return instance.PairSelection[i, j] <= instance.Nodes[i]

    model.pair_first_limits = pyo.Constraint(
        model.A, rule=pair_first_rule
    )

    def pair_second_rule(instance, i, j):
        return instance.PairSelection[i, j] <= instance.Nodes[j]

    model.pair_second_limits = pyo.Constraint(
        model.A, rule=pair_second_rule
    )

    def pair_lower_rule(instance, i, j):
        return (
            instance.PairSelection[i, j]
            >= instance.Nodes[i] + instance.Nodes[j] - 1
        )

    model.pair_lower_limits = pyo.Constraint(
        model.A, rule=pair_lower_rule
    )

    model.dispersion_objective = pyo.Objective(
        expr=model.MinDistance, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.dispersion_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}