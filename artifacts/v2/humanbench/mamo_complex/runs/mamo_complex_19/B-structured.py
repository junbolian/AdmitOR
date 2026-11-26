# IR: {"sets":{"I":"range(params['num_centers'])","J":"range(params['num_stores'])"},"params":{"opening_costs":"I -> real","transportation_costs":"I x J -> real","demands":"J -> nonnegative real","capacities":"I -> nonnegative real","num_centers":"integer, frozen","num_stores":"integer, frozen"},"variables":{"opened[i]":"binary","shipped[i,j]":"nonnegative continuous"},"constraints":["For each j in J: sum(shipped[i,j] for i in I) == demands[j]","For each i in I: sum(shipped[i,j] for j in J) <= capacities[i] * opened[i]"],"objective":"minimize sum(opening_costs[i]*opened[i] for i in I) + sum(transportation_costs[i,j]*shipped[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.centers = pyo.Set(
        initialize=range(params["num_centers"]), ordered=True
    )
    model.stores = pyo.Set(
        initialize=range(params["num_stores"]), ordered=True
    )

    model.opening_cost = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: params["opening_costs"][i],
        within=pyo.Reals,
    )
    model.transportation_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize=lambda mdl, i, j: params["transportation_costs"][i][j],
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize=lambda mdl, j: params["demands"][j],
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize=lambda mdl, i: params["capacities"][i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.centers)
            == mdl.store_demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.stores)
            <= mdl.center_capacity[i] * mdl.opened[i]
        )

    model.capacity_constraints = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transportation_cost[i, j] * model.shipped[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}