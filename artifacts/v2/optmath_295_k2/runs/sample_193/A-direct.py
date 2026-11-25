import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    origins = range(4)
    destinations = range(5)
    products = range(2)

    supply = {
        (0, 0): params["supply_origin0_product0"],
        (0, 1): params["supply_origin0_product1"],
        (1, 0): params["supply_origin1_product0"],
        (1, 1): params["supply_origin1_product1"],
        (2, 0): params["supply_origin2_product0"],
        (2, 1): params["supply_origin2_product1"],
        (3, 0): params["supply_origin3_product0"],
        (3, 1): params["supply_origin3_product1"],
    }

    demand = {
        (0, 0): params["demand_dest0_product0"],
        (0, 1): params["demand_dest0_product1"],
        (1, 0): params["demand_dest1_product0"],
        (1, 1): params["demand_dest1_product1"],
        (2, 0): params["demand_dest2_product0"],
        (2, 1): params["demand_dest2_product1"],
        (3, 0): params["demand_dest3_product0"],
        (3, 1): params["demand_dest3_product1"],
        (4, 0): params["demand_dest4_product0"],
        (4, 1): params["demand_dest4_product1"],
    }

    cost = params["cost_matrix"]
    cap = params["capacity_matrix"]

    model = pyo.ConcreteModel()

    model.O = pyo.Set(initialize=list(origins))
    model.D = pyo.Set(initialize=list(destinations))
    model.P = pyo.Set(initialize=list(products))

    model.x = pyo.Var(model.O, model.D, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            cost[o][d][p] * m.x[o, d, p]
            for o in m.O for d in m.D for p in m.P
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, o, p):
        return sum(m.x[o, d, p] for d in m.D) == supply[(o, p)]

    model.supply_con = pyo.Constraint(model.O, model.P, rule=supply_rule)

    def demand_rule(m, d, p):
        return sum(m.x[o, d, p] for o in m.O) == demand[(d, p)]

    model.demand_con = pyo.Constraint(model.D, model.P, rule=demand_rule)

    def cap_rule(m, o, d):
        return sum(m.x[o, d, p] for p in m.P) <= cap[o][d]

    model.cap_con = pyo.Constraint(model.O, model.D, rule=cap_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}