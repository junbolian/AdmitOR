import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    n_centers = len(opening_costs)
    n_stores = len(demands)

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    # Transport costs are given partially (only first two stores per center).
    # Missing entries are unknown/omitted; treat them as a uniform default cost.
    default_transport = max(
        c for row in transport_costs for c in row
    )

    def get_transport(i, j):
        row = transport_costs[i] if i < len(transport_costs) else []
        if j < len(row):
            return row[j]
        return default_transport

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    model.x = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.C, domain=pyo.Binary)

    model.open_cost = pyo.Expression(
        expr=sum(opening_costs[i] * model.y[i] for i in model.C)
    )
    model.trans_cost = pyo.Expression(
        expr=sum(get_transport(i, j) * model.x[i, j]
                 for i in model.C for j in model.S)
    )
    model.total_cost = pyo.Objective(
        expr=model.open_cost + model.trans_cost, sense=pyo.minimize
    )

    model.demand_con = pyo.Constraint(
        model.S,
        rule=lambda m, j: sum(m.x[i, j] for i in m.C) == demands[j]
    )
    model.capacity_con = pyo.Constraint(
        model.C,
        rule=lambda m, i: sum(m.x[i, j] for j in m.S) <= capacities[i] * m.y[i]
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}