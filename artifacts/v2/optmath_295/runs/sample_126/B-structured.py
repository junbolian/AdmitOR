# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4,5,6]},"params":{"cost[P,C]":"params['cost'][i][j]","capacity[P]":"params['capacity'][i]","demand[C]":"params['demand'][j]","min_contributors[C]":"params['min_contributors'][j]","min_delivery[P]":"params['min_delivery'][i]"},"variables":{"delivery[P,C]":"nonnegative continuous","contributes[P,C]":"binary"},"constraints":["producer_capacity[i]: sum_j delivery[i,j] <= capacity[i]","contract_demand[j]: sum_i delivery[i,j] >= demand[j]","contributor_requirement[j]: sum_i contributes[i,j] >= min_contributors[j]","minimum_delivery[i,j]: delivery[i,j] >= min_delivery[i]*contributes[i,j]","participation_link[i,j]: delivery[i,j] <= capacity[i]*contributes[i,j]"],"objective":"minimize sum_i sum_j cost[i,j]*delivery[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 6)

    model.production_cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda _, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.P,
        initialize=lambda _, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.C,
        initialize=lambda _, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.required_contributors = pyo.Param(
        model.C,
        initialize=lambda _, j: params["min_contributors"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.minimum_delivery_amount = pyo.Param(
        model.P,
        initialize=lambda _, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(
        model.P, model.C, domain=pyo.Binary
    )

    def producer_capacity_rule(block, i):
        return (
            sum(block.delivery[i, j] for j in block.C)
            <= block.producer_capacity[i]
        )

    model.capacity_limits = pyo.Constraint(
        model.P, rule=producer_capacity_rule
    )

    def contract_demand_rule(block, j):
        return (
            sum(block.delivery[i, j] for i in block.P)
            >= block.required_demand[j]
        )

    model.demand_requirements = pyo.Constraint(
        model.C, rule=contract_demand_rule
    )

    def contributor_requirement_rule(block, j):
        return (
            sum(block.contributes[i, j] for i in block.P)
            >= block.required_contributors[j]
        )

    model.contributor_requirements = pyo.Constraint(
        model.C, rule=contributor_requirement_rule
    )

    def minimum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            >= block.minimum_delivery_amount[i] * block.contributes[i, j]
        )

    model.minimum_deliveries = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def participation_link_rule(block, i, j):
        return (
            block.delivery[i, j]
            <= block.producer_capacity[i] * block.contributes[i, j]
        )

    model.participation_links = pyo.Constraint(
        model.P, model.C, rule=participation_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.production_cost[i, j] * model.delivery[i, j]
            for i in model.P
            for j in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}