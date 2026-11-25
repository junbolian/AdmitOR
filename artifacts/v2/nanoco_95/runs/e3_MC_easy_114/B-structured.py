# IR: {"sets":{"N":"range(num_nodes)","A":"range(len(arcs))","arcs":[[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]},"params":{"num_nodes":"positive integer","source":"node in N","sink":"node in N","coords_x":"real[N], geometry metadata","coords_y":"real[N], geometry metadata","arc_capacities":"nonnegative real[A], throughput metadata","arc_unit_costs":"nonnegative real[A], cut weights"},"variables":{"in_source[n]":"binary; 1 iff n belongs to S","crosses[a]":"binary; 1 iff arc a goes from S to T"},"constraints":["in_source[source] = 1","in_source[sink] = 0","crosses[a] >= in_source[tail[a]] - in_source[head[a]] for a in A","crosses[a] <= in_source[tail[a]] for a in A","crosses[a] <= 1 - in_source[head[a]] for a in A"],"objective":"minimize sum(arc_unit_costs[a] * crosses[a] for a in A)","interpretation":"No evacuation flow or required throughput is specified, so capacities impose no additional partition constraints. This minimizes unit-cost cut weights, not physical-capacity cut weights."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    coords_x = params["coords_x"]
    coords_y = params["coords_y"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    arcs = (
        (0, 1),
        (1, 2),
        (1, 4),
        (1, 5),
        (1, 7),
        (2, 3),
        (3, 4),
        (4, 5),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 7),
        (6, 7),
        (7, 8),
        (8, 9),
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_ids = pyo.Set(initialize=range(len(arcs)), ordered=True)

    model.source_node = pyo.Param(initialize=source, within=model.nodes)
    model.sink_node = pyo.Param(initialize=sink, within=model.nodes)

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
    model.arc_capacity = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_capacities[arc_id] for arc_id in range(len(arcs))
        },
        within=pyo.NonNegativeReals,
    )
    model.cut_weight = pyo.Param(
        model.arc_ids,
        initialize={
            arc_id: arc_unit_costs[arc_id] for arc_id in range(len(arcs))
        },
        within=pyo.NonNegativeReals,
    )

    model.in_source = pyo.Var(model.nodes, domain=pyo.Binary)
    model.crosses = pyo.Var(model.arc_ids, domain=pyo.Binary)

    model.source_membership = pyo.Constraint(
        expr=model.in_source[source] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.in_source[sink] == 0
    )

    def crossing_lower_rule(instance, arc_id):
        tail, head = arcs[arc_id]
        return (
            instance.crosses[arc_id]
            >= instance.in_source[tail] - instance.in_source[head]
        )

    def crossing_tail_rule(instance, arc_id):
        tail, _ = arcs[arc_id]
        return instance.crosses[arc_id] <= instance.in_source[tail]

    def crossing_head_rule(instance, arc_id):
        _, head = arcs[arc_id]
        return instance.crosses[arc_id] <= 1 - instance.in_source[head]

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
            model.cut_weight[arc_id] * model.crosses[arc_id]
            for arc_id in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.cut_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}