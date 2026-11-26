# IR: {"sets":{"I":"1..7","J":"1..9"},"params":{"opening_cost":"I; params['opening_cost'][i-1]","transport_cost":"I x J; params['transport_cost'][i-1][j-1]","demand":"J; params['demand'][j-1]","capacity":"I; params['capacity'][i-1]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each j: sum_i shipment[i,j] = demand[j]","For each i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the facility-location problem using zero-based input arrays."""
    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(1, 7)
    model.stores = pyo.RangeSet(1, 9)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            i: params["opening_cost"][i - 1]
            for i in model.centers
        },
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): params["transport_cost"][i - 1][j - 1]
            for i in model.centers
            for j in model.stores
        },
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            j: params["demand"][j - 1]
            for j in model.stores
        },
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            i: params["capacity"][i - 1]
            for i in model.centers
        },
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.centers)
            == mdl.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.stores)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.center_capacity = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}