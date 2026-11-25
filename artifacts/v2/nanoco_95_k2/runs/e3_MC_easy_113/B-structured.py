# IR: {"sets":{"N":"range(params['num_nodes'])","A":"range(17)","arcs":[[0,1],[0,2],[0,3],[0,7],[1,2],[1,5],[2,3],[2,5],[2,6],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{"num_nodes":"node count","source":"source node","sink":"sink node","arc_capacities":"nonnegative capacity indexed by A","arc_unit_costs":"unused unit cost indexed by A","coords_x":"unused x coordinate indexed by N","coords_y":"unused y coordinate indexed by N"},"variables":{"in_source_zone[n]":"Binary; 1 iff n belongs to S","cut_arc[a]":"Binary; 1 iff arc a goes from S to T"},"constraints":["in_source_zone[source] = 1","in_source_zone[sink] = 0","cut_arc[a] >= in_source_zone[tail[a]] - in_source_zone[head[a]] for a in A","cut_arc[a] <= in_source_zone[tail[a]] for a in A","cut_arc[a] <= 1 - in_source_zone[head[a]] for a in A"],"objective":"minimize sum(arc_capacities[a] * cut_arc[a] for a in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    source = params["source"]
    sink = params["sink"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]
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
    model.nodes = pyo.Set(initialize=range(num_nodes), ordered=True)
    model.arc_ids = pyo.Set(initialize=range(len(arcs)), ordered=True)

    model.source_node = pyo.Param(initialize=source, within=model.nodes)
    model.sink_node = pyo.Param(initialize=sink, within=model.nodes)
    model.capacity = pyo.Param(
        model.arc_ids,
        initialize={arc_id: arc_capacities[arc_id]
                    for arc_id in range(len(arcs))},
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arc_ids,
        initialize={arc_id: arc_unit_costs[arc_id]
                    for arc_id in range(len(arcs))},
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

    model.in_source_zone = pyo.Var(model.nodes, domain=pyo.Binary)
    model.cut_arc = pyo.Var(model.arc_ids, domain=pyo.Binary)

    model.source_requirement = pyo.Constraint(
        expr=model.in_source_zone[source] == 1
    )
    model.sink_requirement = pyo.Constraint(
        expr=model.in_source_zone[sink] == 0
    )

    def cut_lower_rule(instance, arc_id):
        tail, head = arcs[arc_id]
        return (
            instance.cut_arc[arc_id]
            >= instance.in_source_zone[tail] - instance.in_source_zone[head]
        )

    def cut_tail_rule(instance, arc_id):
        tail, _ = arcs[arc_id]
        return instance.cut_arc[arc_id] <= instance.in_source_zone[tail]

    def cut_head_rule(instance, arc_id):
        _, head = arcs[arc_id]
        return instance.cut_arc[arc_id] <= 1 - instance.in_source_zone[head]

    model.cut_lower = pyo.Constraint(model.arc_ids, rule=cut_lower_rule)
    model.cut_tail = pyo.Constraint(model.arc_ids, rule=cut_tail_rule)
    model.cut_head = pyo.Constraint(model.arc_ids, rule=cut_head_rule)

    model.total_cut_capacity = pyo.Objective(
        expr=sum(
            model.capacity[arc_id] * model.cut_arc[arc_id]
            for arc_id in model.arc_ids
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when its default solution loading finds no
        # feasible solution. Still determine success by objective retrieval.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cut_capacity))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}