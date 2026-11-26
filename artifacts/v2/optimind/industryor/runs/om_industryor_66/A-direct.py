import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_A_min = params["supply_A_min"]
    supply_B_min = params["supply_B_min"]
    demand_1 = params["demand_1"]
    demand_2 = params["demand_2"]
    demand_3 = params["demand_3"]
    distance_A1 = params["distance_A1"]
    distance_A2 = params["distance_A2"]
    distance_A3 = params["distance_A3"]
    distance_B1 = params["distance_B1"]
    distance_B2 = params["distance_B2"]
    distance_B3 = params["distance_B3"]

    yards = ["A", "B"]
    areas = ["1", "2", "3"]
    routes = [(y, a) for y in yards for a in areas]

    dist = {
        ("A", "1"): distance_A1,
        ("A", "2"): distance_A2,
        ("A", "3"): distance_A3,
        ("B", "1"): distance_B1,
        ("B", "2"): distance_B2,
        ("B", "3"): distance_B3,
    }
    supply_min = {"A": supply_A_min, "B": supply_B_min}
    demand = {"1": demand_1, "2": demand_2, "3": demand_3}

    model = pyo.ConcreteModel()

    model.routes = pyo.Set(initialize=routes, dimen=2)
    model.x = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(dist[r] * m.x[r] for r in m.routes)

    model.transport_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, y):
        return sum(m.x[(y, a)] for a in areas) >= supply_min[y]

    model.supply_con = pyo.Constraint(yards, rule=supply_rule)

    def demand_rule(m, a):
        return sum(m.x[(y, a)] for y in yards) == demand[a]

    model.demand_con = pyo.Constraint(areas, rule=demand_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.transport_cost))
    return {"objective": obj_val, "status": "optimal"}