import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    employees = [0, 1, 2, 3, 4, 5]

    skilled = [1, 2, 3, 4]

    available = {
        0: [],
        1: [(0, 0), (0, 1), (1, 0), (1, 1)],
        2: [(0, 0), (0, 1), (1, 0), (1, 1)],
        3: [(0, 0), (1, 0)],
        4: [(0, 0), (0, 1), (1, 0), (1, 1)],
        5: [],
    }

    pref_cost = {
        1: params["pref_cost_E1"],
        2: params["pref_cost_E2"],
        3: params["pref_cost_E3"],
        4: params["pref_cost_E4"],
    }

    demand = {
        (0, 0): params["demand_R0_S0"],
        (0, 1): params["demand_R0_S1"],
        (1, 0): params["demand_R1_S0"],
        (1, 1): params["demand_R1_S1"],
    }

    penalty = params["penalty"]

    model = pyo.ConcreteModel()

    rs_pairs = [(0, 0), (0, 1), (1, 0), (1, 1)]

    arcs = []
    for e in employees:
        if e in skilled:
            for (r, s) in available[e]:
                arcs.append((e, r, s))

    model.ARC = pyo.Set(initialize=arcs, dimen=3)
    model.RS = pyo.Set(initialize=rs_pairs, dimen=2)

    model.x = pyo.Var(model.ARC, domain=pyo.Binary)
    model.u = pyo.Var(model.RS, domain=pyo.NonNegativeIntegers)

    def assigned_to(mdl, r, s):
        return sum(mdl.x[e, rr, ss] for (e, rr, ss) in arcs if rr == r and ss == s)

    def demand_rule(mdl, r, s):
        return assigned_to(mdl, r, s) + mdl.u[r, s] == demand[(r, s)]
    model.demand_con = pyo.Constraint(model.RS, rule=demand_rule)

    def once_rule(mdl, e):
        expr = sum(mdl.x[ee, r, s] for (ee, r, s) in arcs if ee == e)
        return expr <= 1
    model.once_con = pyo.Constraint(employees, rule=once_rule)

    def obj_rule(mdl):
        assign_cost = sum(pref_cost[e] * mdl.x[e, r, s] for (e, r, s) in arcs)
        pen_cost = sum(penalty * mdl.u[r, s] for (r, s) in rs_pairs)
        return assign_cost + pen_cost
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}