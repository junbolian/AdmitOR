# IR: {"sets":{"N":"range(num_nodes)","A":"[(i,j) for i in N for j in N if i != j], in lexicographic order"},"params":{"distances":"directed distance vector indexed by A","num_selected":"required selection count","num_nodes":"number of nodes"},"variables":{"x[i]":"Binary, i in N","y[i,j]":"Binary, (i,j) in A"},"constraints":["sum(x[i] for i in N) == num_selected","y[i,j] <= x[i] for (i,j) in A","y[i,j] <= x[j] for (i,j) in A","y[i,j] >= x[i] + x[j] - 1 for (i,j) in A"],"objective":"maximize sum(distances[i,j] * y[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_selected = params["num_selected"]
    distances = params["distances"]

    nodes = list(range(num_nodes))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    if len(distances) != len(arcs):
        return {"objective": None, "status": "invalid_distances_length"}

    distance_data = {
        arc: distances[position] for position, arc in enumerate(arcs)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(
        dimen=2, initialize=arcs, within=model.nodes * model.nodes, ordered=True
    )
    model.distance = pyo.Param(
        model.arcs, initialize=distance_data, within=pyo.Reals
    )
    model.required_count = pyo.Param(
        initialize=num_selected, within=pyo.Reals
    )

    model.x = pyo.Var(model.nodes, domain=pyo.Binary)
    model.y = pyo.Var(model.arcs, domain=pyo.Binary)

    model.selection_count = pyo.Constraint(
        expr=pyo.quicksum(model.x[i] for i in model.nodes)
        == model.required_count
    )

    def pair_first_upper_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[i]

    def pair_second_upper_rule(instance, i, j):
        return instance.y[i, j] <= instance.x[j]

    def pair_lower_rule(instance, i, j):
        return instance.y[i, j] >= instance.x[i] + instance.x[j] - 1

    model.pair_first_upper = pyo.Constraint(
        model.arcs, rule=pair_first_upper_rule
    )
    model.pair_second_upper = pyo.Constraint(
        model.arcs, rule=pair_second_upper_rule
    )
    model.pair_lower = pyo.Constraint(
        model.arcs, rule=pair_lower_rule
    )

    model.total_dispersion = pyo.Objective(
        expr=pyo.quicksum(
            model.distance[i, j] * model.y[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_dispersion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}