import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 8
    nodes = list(range(n))
    stores = list(range(1, n))

    travel_time = params["travel_time"]

    tw_earliest = [
        params["tw_0_earliest"],
        params["tw_1_earliest"],
        params["tw_2_earliest"],
        params["tw_3_earliest"],
        params["tw_4_earliest"],
        params["tw_5_earliest"],
        params["tw_6_earliest"],
        params["tw_7_earliest"],
    ]
    tw_latest = [
        params["tw_0_latest"],
        params["tw_1_latest"],
        params["tw_2_latest"],
        params["tw_3_latest"],
        params["tw_4_latest"],
        params["tw_5_latest"],
        params["tw_6_latest"],
        params["tw_7_latest"],
    ]

    service_time = params["service_time"]
    max_duration = params["max_shelf_life_window"]

    big_m = max_duration + sum(travel_time[i][j] for i in nodes for j in nodes)

    model = pyo.ConcreteModel()

    model.arc = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # Departure/arrival time at each node (for depot, this is the departure time)
    model.start = pyo.Var(nodes, domain=pyo.NonNegativeReals)
    # Explicit return time to the depot
    model.depot_return = pyo.Var(domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            travel_time[i][j] * m.arc[i, j]
            for i in nodes
            for j in nodes
            if i != j
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def in_rule(m, j):
        return sum(m.arc[i, j] for i in nodes if i != j) == 1

    model.in_cons = pyo.Constraint(stores, rule=in_rule)

    def out_rule(m, i):
        return sum(m.arc[i, j] for j in nodes if j != i) == 1

    model.out_cons = pyo.Constraint(stores, rule=out_rule)

    model.depot_out = pyo.Constraint(
        expr=sum(model.arc[0, j] for j in stores) == 1
    )
    model.depot_in = pyo.Constraint(
        expr=sum(model.arc[i, 0] for i in stores) == 1
    )

    # Time windows for all nodes. For depot, start[0] is the departure time.
    def tw_rule(m, j):
        return pyo.inequality(tw_earliest[j], m.start[j], tw_latest[j])

    model.tw_cons = pyo.Constraint(nodes, rule=tw_rule)

    # Time propagation for arcs leaving the depot (i=0) use start[0]
    # For arcs entering the depot (j=0), use depot_return
    def time_prop_rule(m, i, j):
        if i == j:
            return pyo.Constraint.Skip
        if i == 0:
            return m.start[j] >= m.start[0] + service_time + travel_time[0][j] - big_m * (1 - m.arc[0, j])
        if j == 0:
            return m.depot_return >= m.start[i] + service_time + travel_time[i][0] - big_m * (1 - m.arc[i, 0])
        return m.start[j] >= m.start[i] + service_time + travel_time[i][j] - big_m * (1 - m.arc[i, j])

    model.time_prop = pyo.Constraint(nodes, nodes, rule=time_prop_rule)

    # Route duration: depot_return within max shelf-life window
    model.max_dur = pyo.Constraint(
        expr=model.depot_return <= max_duration
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}