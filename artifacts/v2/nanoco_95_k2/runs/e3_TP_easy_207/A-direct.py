import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hubs = [0, 1, 2]
    areas = [3, 4, 5, 6]
    arcs = [(h, a) for h in hubs for a in areas]

    supply = {
        0: params["supply_hub0"],
        1: params["supply_hub1"],
        2: params["supply_hub2"],
    }
    demand = {
        3: params["demand_area3"],
        4: params["demand_area4"],
        5: params["demand_area5"],
        6: params["demand_area6"],
    }
    cap = {(h, a): params["capacity_arc_%d_%d" % (h, a)] for (h, a) in arcs}
    cost = {(h, a): params["cost_arc_%d_%d" % (h, a)] for (h, a) in arcs}

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.HUB = pyo.Set(initialize=hubs)
    model.AREA = pyo.Set(initialize=areas)

    model.x = pyo.Var(model.ARC, domain=pyo.NonNegativeReals, bounds=lambda m, h, a: (0, cap[(h, a)]))

    def obj_rule(m):
        return sum(cost[(h, a)] * m.x[(h, a)] for (h, a) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, h):
        return sum(m.x[(h, a)] for a in areas) == supply[h]

    model.supply_con = pyo.Constraint(model.HUB, rule=supply_rule)

    def demand_rule(m, a):
        return sum(m.x[(h, a)] for h in hubs) == demand[a]

    model.demand_con = pyo.Constraint(model.AREA, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}