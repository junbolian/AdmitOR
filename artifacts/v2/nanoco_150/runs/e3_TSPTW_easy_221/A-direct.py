import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_nodes"])
    nodes = list(range(n))
    H = list(range(1, n))

    travel = {}
    for i in nodes:
        row = params[f"travel_time_{i}"]
        for j in nodes:
            travel[i, j] = row[j]

    w_start = {}
    w_end = {}
    for i in nodes:
        w_start[i] = params[f"window_{i}_start"]
        w_end[i] = params[f"window_{i}_end"]
    horizon = params["horizon"]
    service = params["service_time"]

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=nodes)
    model.H = pyo.Set(initialize=H)

    model.x = pyo.Var(model.V, model.V, domain=pyo.Binary)
    model.t = pyo.Var(model.V, domain=pyo.NonNegativeReals)
    model.u = pyo.Var(model.H, domain=pyo.NonNegativeReals, bounds=(1, len(H)))

    for i in nodes:
        model.x[i, i].fix(0)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.V if j != i) == 1
    model.out_con = pyo.Constraint(model.H, rule=out_rule)

    def in_rule(m, i):
        return sum(m.x[j, i] for j in m.V if j != i) == 1
    model.in_con = pyo.Constraint(model.H, rule=in_rule)

    model.hub_out = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.V if j != 0) == 1)
    model.hub_in = pyo.Constraint(
        expr=sum(model.x[j, 0] for j in model.V if j != 0) == 1)

    for i in nodes:
        model.t[i].setlb(w_start[i])
        model.t[i].setub(w_end[i])

    model.start_time = pyo.Constraint(expr=model.t[0] <= w_end[0])

    M = horizon + max(travel[i, j] for i in nodes for j in nodes) + service
    for i in nodes:
        for j in nodes:
            if i != j:
                model.add_component(
                    f"time_{i}_{j}",
                    pyo.Constraint(
                        expr=model.t[j] >= model.t[i] + service + travel[i, j]
                        - M * (1 - model.x[i, j])))

    model.horizon_con = pyo.Constraint(expr=model.t[0] <= horizon)

    for i in H:
        for j in H:
            if i != j:
                model.add_component(
                    f"mtz_{i}_{j}",
                    pyo.Constraint(
                        expr=model.u[i] - model.u[j] + len(H) * model.x[i, j]
                        <= len(H) - 1))

    def obj_rule(m):
        return sum(travel[i, j] * m.x[i, j]
                   for i in nodes for j in nodes if i != j)
    model.total_travel = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_travel))
    return {"objective": obj_val, "status": "optimal"}