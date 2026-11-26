import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    num_centers = params["num_centers"]
    num_stores = params["num_stores"]

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, num_centers)
    model.stores = pyo.RangeSet(1, num_stores)

    model.x = pyo.Var(model.centers, model.stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.centers, domain=pyo.Binary)

    model.opening_cost_expr = pyo.Expression(
        expr=sum(opening_costs[i - 1] * model.y[i] for i in model.centers)
    )
    model.transport_cost_expr = pyo.Expression(
        expr=sum(
            transport_costs[i - 1][j - 1] * model.x[i, j]
            for i in model.centers
            for j in model.stores
        )
    )
    model.total_cost = pyo.Objective(
        expr=model.opening_cost_expr + model.transport_cost_expr,
        sense=pyo.minimize,
    )

    model.demand_rule = pyo.Constraint(
        model.stores,
        rule=lambda m, j: sum(m.x[i, j] for i in m.centers) == demands[j - 1],
    )

    model.capacity_rule = pyo.Constraint(
        model.centers,
        rule=lambda m, i: sum(m.x[i, j] for j in m.stores) <= capacities[i - 1] * m.y[i],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}