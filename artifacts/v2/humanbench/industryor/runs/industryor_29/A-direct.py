import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_rate = params["cost_rate"]
    distance = params["distance"]
    truck_capacity = params["truck_capacity"]

    warehouses = ["Verona", "Perugia", "Rome", "Pescara", "Taranto", "La Spezia"]
    ports = ["Genoa", "Venice", "Ancona", "Naples", "Bari"]

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=warehouses)
    model.P = pyo.Set(initialize=ports)

    model.x = pyo.Var(model.W, model.P, within=pyo.NonNegativeIntegers)

    def obj_rule(mdl):
        return sum(
            mdl.x[w, p] * (distance[warehouses.index(w)][ports.index(p)] * cost_rate / truck_capacity)
            for w in mdl.W for p in mdl.P
        )
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.supply_con = pyo.Constraint(
        model.W,
        rule=lambda mdl, w: sum(mdl.x[w, p] for p in mdl.P) <= supply[w]
    )
    model.demand_con = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: sum(mdl.x[w, p] for w in mdl.W) >= demand[p]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}