import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    distance = params["distance"]
    cost_rate = params["cost_rate"]
    truck_capacity = params["truck_capacity"]

    warehouses = list(supply)
    ports = list(demand)

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=warehouses)
    model.P = pyo.Set(initialize=ports)

    # x[i,j] = number of containers shipped from warehouse i to port j
    model.x = pyo.Var(model.W, model.P, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            cost_rate * distance[w][p] * m.x[w, p]
            for w in m.W
            for p in m.P
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.supply_limit = pyo.Constraint(
        model.W,
        rule=lambda m, w: sum(m.x[w, p] for p in m.P) <= supply[w],
    )

    model.demand_satisfied = pyo.Constraint(
        model.P,
        rule=lambda m, p: sum(m.x[w, p] for w in m.W) == demand[p],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}