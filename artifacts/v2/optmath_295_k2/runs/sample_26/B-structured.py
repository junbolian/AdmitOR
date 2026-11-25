# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3]},"params":{"capacity[P]":"params['capacity'][i]","demand[C]":"params['demand'][j]","min_delivery[P]":"params['min_delivery'][i]","cost[P,C]":"params['cost'][i][j]"},"variables":{"delivery[P,C]":"continuous nonnegative","contributes[P,C]":"binary"},"constraints":["forall i: sum_j delivery[i,j] <= capacity[i]","forall j: sum_i delivery[i,j] >= demand[j]","forall j: sum_i contributes[i,j] >= 2","forall i,j: delivery[i,j] >= min_delivery[i]*contributes[i,j]","forall i,j: delivery[i,j] <= capacity[i]*contributes[i,j]"],"objective":"minimize sum_i,j cost[i,j]*delivery[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using producer-indexed vectors and a producer-by-contract cost matrix."""
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 3)
    model.contracts = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(
        model.producers,
        initialize=lambda model, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize=lambda model, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize=lambda model, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda model, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.NonNegativeReals,
    )
    model.contributes = pyo.Var(
        model.producers,
        model.contracts,
        domain=pyo.Binary,
    )

    model.capacity_limit = pyo.Constraint(
        model.producers,
        rule=lambda model, i: (
            sum(model.delivery[i, j] for j in model.contracts)
            <= model.capacity[i]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.contracts,
        rule=lambda model, j: (
            sum(model.delivery[i, j] for i in model.producers)
            >= model.demand[j]
        ),
    )
    model.producer_count_requirement = pyo.Constraint(
        model.contracts,
        rule=lambda model, j: (
            sum(model.contributes[i, j] for i in model.producers) >= 2
        ),
    )
    model.minimum_contribution = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda model, i, j: (
            model.delivery[i, j]
            >= model.min_delivery[i] * model.contributes[i, j]
        ),
    )
    model.contribution_link = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=lambda model, i, j: (
            model.delivery[i, j]
            <= model.capacity[i] * model.contributes[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.delivery[i, j]
            for i in model.producers
            for j in model.contracts
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