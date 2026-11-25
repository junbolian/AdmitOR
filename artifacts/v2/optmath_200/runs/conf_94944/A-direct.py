import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    link_capacity = params["link_capacity"]

    W = len(supply)
    S = len(demand)
    P = len(supply[0])

    model = pyo.ConcreteModel()

    model.WAREHOUSES = pyo.RangeSet(W)
    model.STORES = pyo.RangeSet(S)
    model.PRODUCTS = pyo.RangeSet(P)

    model.x = pyo.Var(
        model.WAREHOUSES, model.STORES, model.PRODUCTS,
        within=pyo.NonNegativeReals,
    )

    def obj_rule(mdl):
        return sum(
            cost[p][w][s] * mdl.x[w, s, p]
            for w in mdl.WAREHOUSES
            for s in mdl.STORES
            for p in mdl.PRODUCTS
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Warehouse supply limits per product
    def supply_rule(mdl, w, p):
        return sum(mdl.x[w, s, p] for s in mdl.STORES) <= supply[w][p]
    model.supply_limit = pyo.Constraint(
        model.WAREHOUSES, model.PRODUCTS, rule=supply_rule
    )

    # Store demand must be met per product
    def demand_rule(mdl, s, p):
        return sum(mdl.x[w, s, p] for w in mdl.WAREHOUSES) == demand[s][p]
    model.demand_sat = pyo.Constraint(
        model.STORES, model.PRODUCTS, rule=demand_rule
    )

    # Combined link capacity between warehouse and store
    def link_rule(mdl, w, s):
        return sum(mdl.x[w, s, p] for p in mdl.PRODUCTS) <= link_capacity[w][s]
    model.link_limit = pyo.Constraint(
        model.WAREHOUSES, model.STORES, rule=link_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}