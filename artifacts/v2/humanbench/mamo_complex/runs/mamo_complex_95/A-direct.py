import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = list(params["opening_costs"])
    transport_costs = list(params["transport_costs"])
    demands = list(params["demands"])
    capacities = list(params["capacities"])

    n_centers = len(opening_costs)
    n_stores = len(demands)

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    model = pyo.ConcreteModel()

    model.open_center = pyo.Var(centers, domain=pyo.Binary)
    model.ship = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)

    # Objective: total fixed opening cost + transportation cost
    model.total_cost = pyo.Expression(
        expr=sum(opening_costs[i] * model.open_center[i] for i in centers)
        + sum(transport_costs[i][j] * model.ship[i, j] for i in centers for j in stores)
    )

    # Each store's demand must be met
    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda m, j: sum(m.ship[i, j] for i in centers) == demands[j],
    )

    # Capacity constraints: cannot ship more than capacity of open centers
    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda m, i: sum(m.ship[i, j] for j in stores)
        <= capacities[i] * m.open_center[i],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}