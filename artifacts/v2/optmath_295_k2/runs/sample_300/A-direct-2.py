import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_warehouses = 5
    num_stores = 6
    num_products = 2

    warehouses = list(range(num_warehouses))
    stores = list(range(num_stores))
    products = list(range(num_products))

    supply = {
        0: params["supply_product0"],
        1: params["supply_product1"],
    }
    demand = {
        0: params["demand_product0"],
        1: params["demand_product1"],
    }
    cost = {
        0: params["transport_cost_product0"],
        1: params["transport_cost_product1"],
    }
    cap = params["link_capacity"]

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.S = pyo.Set(initialize=stores)
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.W, model.S, model.P, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            cost[p][w][s] * m.x[w, s, p]
            for w in m.W for s in m.S for p in m.P
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, w, p):
        return sum(m.x[w, s, p] for s in m.S) <= supply[p][w]
    model.supply_con = pyo.Constraint(model.W, model.P, rule=supply_rule)

    def demand_rule(m, s, p):
        return sum(m.x[w, s, p] for w in m.W) >= demand[p][s]
    model.demand_con = pyo.Constraint(model.S, model.P, rule=demand_rule)

    def cap_rule(m, w, s):
        return sum(m.x[w, s, p] for p in m.P) <= cap[w][s]
    model.cap_con = pyo.Constraint(model.W, model.S, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}