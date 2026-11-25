import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    distance_matrix = params["distance_matrix"]
    time_windows = params["time_windows"]
    service_times = params["service_times"]
    horizon = params["horizon"]

    nodes = list(range(num_nodes))
    stations = nodes[1:]

    model = pyo.ConcreteModel()

    # Binary arc variables
    model.x = pyo.Var(nodes, nodes, domain=pyo.Binary)

    # Continuous time variables (arrival time at each node)
    model.t = pyo.Var(nodes, domain=pyo.NonNegativeReals)

    # Objective: minimize total transport distance
    def obj_rule(mdl):
        return sum(
            distance_matrix[i][j] * mdl.x[i, j]
            for i in nodes
            for j in nodes
            if i != j
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each station has exactly one outgoing arc
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in nodes if j != i) == 1

    model.out_con = pyo.Constraint(stations, rule=out_rule)

    # Each station has exactly one incoming arc
    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in nodes if i != j) == 1

    model.in_con = pyo.Constraint(stations, rule=in_rule)

    # Hub: exactly one departure and one return
    model.hub_out = pyo.Constraint(
        expr=sum(model.x[0, j] for j in stations) == 1
    )
    model.hub_in = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in stations) == 1
    )

    # Time window constraints (strict bounds on arrival times)
    def tw_rule(mdl, i):
        return pyo.inequality(
            time_windows[i][0], mdl.t[i], time_windows[i][1]
        )

    model.tw_con = pyo.Constraint(nodes, rule=tw_rule)

    # Big-M: must exceed any possible arrival time minus any other arrival
    # time so that the constraint is always satisfiable when x[i,j]=0.
    max_tw_end = max(time_windows[i][1] for i in nodes)
    max_dist = max(
        distance_matrix[i][j]
        for i in nodes
        for j in nodes
        if i != j
    )
    max_service = max(service_times) if service_times else 0
    big_m = max_tw_end + max_dist + max_service + horizon + 1.0

    # Arc time propagation: t[i] + service[i] + dist[i][j] <= t[j] + M*(1-x[i,j])
    def arc_time_rule(mdl, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            mdl.t[i]
            + service_times[i]
            + distance_matrix[i][j]
            <= mdl.t[j]
            + big_m * (1 - mdl.x[i, j])
        )

    model.arc_time_con = pyo.Constraint(nodes, nodes, rule=arc_time_rule)

    # Fix hub departure time to 0 (start of shift)
    model.hub_time = pyo.Constraint(expr=model.t[0] == 0)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}