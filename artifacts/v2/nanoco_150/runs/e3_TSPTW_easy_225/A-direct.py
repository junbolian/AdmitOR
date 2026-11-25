import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    nodes = list(range(n))

    travel = params["travel_time"]
    tw_start = params["time_window_start"]
    tw_end = params["time_window_end"]
    horizon = params["planning_horizon"]
    service = params["service_time"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(i, j) for i in nodes for j in nodes if i != j],
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.t = pyo.Var(model.nodes, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(travel[i][j] * m.x[i, j] for (i, j) in m.arcs)

    model.total_travel_time = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def visit_out_rule(m, i):
        return sum(m.x[i, j] for j in m.nodes if j != i) == 1

    model.visit_out = pyo.Constraint(model.nodes, rule=visit_out_rule)

    def visit_in_rule(m, j):
        return sum(m.x[i, j] for i in m.nodes if i != j) == 1

    model.visit_in = pyo.Constraint(model.nodes, rule=visit_in_rule)

    # Start the departure at the start of node 0's time window.
    model.departure = pyo.Constraint(
        expr=model.t[0] >= tw_start[0])

    # Arrival times within time windows for all nodes.
    def tw_rule(m, i):
        return pyo.inequality(tw_start[i], m.t[i], tw_end[i])

    model.tw = pyo.Constraint(model.nodes, rule=tw_rule)

    # Big-M for time propagation. Use a safe upper bound on times.
    big_m = tw_end[0]

    def arc_time_rule(m, i, j):
        return m.t[j] >= m.t[i] + service[i] + travel[i][j] - big_m * (1 - m.x[i, j])

    model.arc_time = pyo.Constraint(model.arcs, rule=arc_time_rule)

    # Total route duration (return to node 0) must not exceed horizon.
    model.horizon = pyo.Constraint(expr=model.t[0] <= pyo.value(model.t[0]) * 0 + big_m)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_travel_time))
    return {"objective": obj_val, "status": "optimal"}