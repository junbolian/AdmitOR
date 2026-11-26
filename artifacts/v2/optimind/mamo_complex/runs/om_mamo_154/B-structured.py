# IR: {"sets":{"I":"0..8 centers","J":"0..7 stores"},"params":{"opening_costs":"F[i] from params","transport_costs":"c[i,j] from params","demands":"d[j] from params","capacities":"u[i] from params"},"variables":{"y[i]":"binary; center open","x[i,j]":"nonnegative continuous; units shipped"},"constraints":["sum(i in I, x[i,j]) = d[j] for each j in J","sum(j in J, x[i,j]) <= u[i]*y[i] for each i in I"],"objective":"minimize sum(i in I, F[i]*y[i]) + sum(i in I,j in J, c[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the facility-location problem using zero-based input sequences."""
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.centers = pyo.Set(initialize=range(9), ordered=True)
    model.stores = pyo.Set(initialize=range(8), ordered=True)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize={i: opening_costs[i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): transport_costs[i][j]
            for i in model.centers
            for j in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demands[j] for j in model.stores},
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacities[i] for i in model.centers},
        within=pyo.NonNegativeReals,
    )

    model.is_open = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.center_capacity[i] * mdl.is_open[i]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.is_open[i]
                for i in model.centers
            )
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}