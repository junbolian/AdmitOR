# IR: {"sets":{"N":"0,...,num_nodes-1","A":"17 directed arcs in the supplied order"},"params":{"arc_capacities":"nonnegative capacity indexed by A","arc_unit_costs":"unused route cost indexed by A","num_nodes":"positive integer","source":"node in N","sink":"node in N","coords_x":"unused x coordinate indexed by N","coords_y":"unused y coordinate indexed by N"},"variables":{"in_S[n]":"binary for n in N","crosses[a]":"binary for a in A"},"constraints":["in_S[source] = 1","in_S[sink] = 0","crosses[a] >= in_S[tail[a]] - in_S[head[a]]","crosses[a] <= in_S[tail[a]]","crosses[a] <= 1 - in_S[head[a]]"],"objective":"minimize sum(arc_capacities[a] * crosses[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    coords_x = params["coords_x"]
    coords_y = params["coords_y"]

    arcs = (
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 7),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 5),
        (2, 6),
        (3, 4),
        (3, 5),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 6),
        (5, 7),
        (6, 7),
    )

    model = pyo.ConcreteModel()
    model.node_count = pyo.Param(
        initialize=num_nodes, within=pyo.PositiveIntegers
    )
    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.arc_ids = pyo.RangeSet(0, len(arcs) - 1)

    model.source_node = pyo.Param(initialize=source, within=model.nodes)
    model.sink_node = pyo.Param(initialize=sink, within=model.nodes)
    model.capacity = pyo.Param(
        model.arc_ids,
        initialize={a: arc_capacities[a] for a in range(len(arcs))},
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arc_ids,
        initialize={a: arc_unit_costs[a] for a in range(len(arcs))},
        within=pyo.Reals,
    )
    model.x_coordinate = pyo.Param(
        model.nodes,
        initialize={node: coords_x[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )
    model.y_coordinate = pyo.Param(
        model.nodes,
        initialize={node: coords_y[node] for node in range(num_nodes)},
        within=pyo.Reals,
    )

    model.in_S = pyo.Var(model.nodes, domain=pyo.Binary)
    model.crosses = pyo.Var(model.arc_ids, domain=pyo.Binary)

    model.source_membership = pyo.Constraint(
        expr=model.in_S[source] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.in_S[sink] == 0
    )

    def crossing_lower_rule(instance, a):
        tail, head = arcs[a]
        return (
            instance.crosses[a]
            >= instance.in_S[tail] - instance.in_S[head]
        )

    def crossing_tail_rule(instance, a):
        tail, _ = arcs[a]
        return instance.crosses[a] <= instance.in_S[tail]

    def crossing_head_rule(instance, a):
        _, head = arcs[a]
        return instance.crosses[a] <= 1 - instance.in_S[head]

    model.crossing_lower = pyo.Constraint(
        model.arc_ids, rule=crossing_lower_rule
    )
    model.crossing_tail = pyo.Constraint(
        model.arc_ids, rule=crossing_tail_rule
    )
    model.crossing_head = pyo.Constraint(
        model.arc_ids, rule=crossing_head_rule
    )

    model.cut_objective = pyo.Objective(
        expr=sum(
            model.capacity[a] * model.crosses[a]
            for a in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}