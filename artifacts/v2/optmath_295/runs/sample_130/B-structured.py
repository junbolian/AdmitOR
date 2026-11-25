# IR: {"sets":{"I":[0,1,2,3],"J":[0,1,2,3,4]},"params":{"capacity":"params['capacity'][i] >= 0","demand":"params['demand'][j] >= 0","min_delivery":"params['min_delivery'][i] >= 0","cost":"params['cost'][i][j]"},"variables":{"delivery[i,j]":"continuous >= 0","contributes[i,j]":"binary"},"constraints":["For each i: sum_j delivery[i,j] <= capacity[i]","For each j: sum_i delivery[i,j] >= demand[j]","For each j: sum_i contributes[i,j] >= 2","For each i,j: delivery[i,j] >= min_delivery[i]*contributes[i,j]","For each i,j: delivery[i,j] <= capacity[i]*contributes[i,j]"],"objective":"minimize sum_i sum_j cost[i,j]*delivery[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using producer-indexed vectors and a nested cost matrix."""
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 3)
    model.contracts = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.producers,
        initialize={i: capacity[i] for i in model.producers},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize={j: demand[j] for j in model.contracts},
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize={i: min_delivery[i] for i in model.producers},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize={
            (i, j): cost[i][j]
            for i in model.producers
            for j in model.contracts
        },
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.producers, model.contracts, domain=pyo.Binary
    )

    def capacity_rule(block, i):
        return (
            sum(block.delivery[i, j] for j in block.contracts)
            <= block.capacity[i]
        )

    model.capacity_limits = pyo.Constraint(
        model.producers, rule=capacity_rule
    )

    def demand_rule(block, j):
        return (
            sum(block.delivery[i, j] for i in block.producers)
            >= block.demand[j]
        )

    model.contract_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def contributors_rule(block, j):
        return sum(
            block.contributes[i, j] for i in block.producers
        ) >= 2

    model.minimum_contributors = pyo.Constraint(
        model.contracts, rule=contributors_rule
    )

    def minimum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            >= block.min_delivery[i] * block.contributes[i, j]
        )

    model.delivery_lower_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def maximum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            <= block.capacity[i] * block.contributes[i, j]
        )

    model.delivery_upper_links = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=maximum_delivery_rule,
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}