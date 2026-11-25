# IR: {"sets":{"nodes":"0..7","routes":"0..16","dimensions":"0..1","arcs":[[0,1],[0,2],[0,3],[0,7],[1,2],[1,5],[2,3],[2,5],[2,6],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6],[5,7],[6,7]]},"params":{"arc_capacities":"nonnegative route capacities from params","arc_unit_costs":"route costs from params; unused in optimization","coords":"immutable node coordinates from params; unused in optimization"},"variables":{"in_source_zone[node]":"binary; 1 iff node belongs to S","cut_arc[route]":"binary; 1 iff route goes from S to T"},"constraints":["in_source_zone[0] = 1","in_source_zone[7] = 0","cut_arc[r] >= in_source_zone[tail[r]] - in_source_zone[head[r]]","cut_arc[r] <= in_source_zone[tail[r]]","cut_arc[r] <= 1 - in_source_zone[head[r]]"],"objective":"minimize sum(arc_capacities[r] * cut_arc[r] for r in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the directed minimum-cut problem using route-order input arrays."""
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

    capacities = tuple(params["arc_capacities"])
    unit_costs = tuple(params["arc_unit_costs"])
    coordinates = tuple(tuple(point) for point in params["coords"])

    if len(capacities) != len(arcs) or len(unit_costs) != len(arcs):
        return {"objective": None, "status": "invalid_route_data"}

    if len(coordinates) != 8 or any(
        len(point) != 2 for point in coordinates
    ):
        return {"objective": None, "status": "invalid_coordinates"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.routes = pyo.RangeSet(0, 16)
    model.dimensions = pyo.RangeSet(0, 1)

    model.arc_capacities = pyo.Param(
        model.routes,
        initialize=lambda mdl, route: capacities[route],
        within=pyo.NonNegativeReals,
        mutable=False,
    )
    model.arc_unit_costs = pyo.Param(
        model.routes,
        initialize=lambda mdl, route: unit_costs[route],
        within=pyo.Reals,
        mutable=False,
    )
    model.coords = pyo.Param(
        model.nodes,
        model.dimensions,
        initialize=lambda mdl, node, dimension: coordinates[node][dimension],
        within=pyo.Reals,
        mutable=False,
    )

    model.in_source_zone = pyo.Var(model.nodes, domain=pyo.Binary)
    model.cut_arc = pyo.Var(model.routes, domain=pyo.Binary)

    model.source_membership = pyo.Constraint(
        expr=model.in_source_zone[0] == 1
    )
    model.sink_membership = pyo.Constraint(
        expr=model.in_source_zone[7] == 0
    )

    def cut_lower_rule(mdl, route):
        tail, head = arcs[route]
        return (
            mdl.cut_arc[route]
            >= mdl.in_source_zone[tail] - mdl.in_source_zone[head]
        )

    def cut_tail_upper_rule(mdl, route):
        tail, _ = arcs[route]
        return mdl.cut_arc[route] <= mdl.in_source_zone[tail]

    def cut_head_upper_rule(mdl, route):
        _, head = arcs[route]
        return mdl.cut_arc[route] <= 1 - mdl.in_source_zone[head]

    model.cut_lower = pyo.Constraint(model.routes, rule=cut_lower_rule)
    model.cut_tail_upper = pyo.Constraint(
        model.routes, rule=cut_tail_upper_rule
    )
    model.cut_head_upper = pyo.Constraint(
        model.routes, rule=cut_head_upper_rule
    )

    model.total_cut_capacity = pyo.Objective(
        expr=sum(
            model.arc_capacities[route] * model.cut_arc[route]
            for route in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cut_capacity))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}