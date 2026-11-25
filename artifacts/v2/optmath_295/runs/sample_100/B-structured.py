# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4,5]},"params":{"capacity[i]":"params['capacity'][i], nonnegative","demand[j]":"params['demand'][j], nonnegative","cost[i,j]":"params['cost'][i][j], real","min_delivery[i]":"params['min_delivery'][i], nonnegative","min_contributors[j]":"params['min_contributors'][j], nonnegative integer"},"variables":{"delivery[i,j]":"nonnegative continuous","selected[i,j]":"binary"},"constraints":["For each i: sum_j delivery[i,j] <= capacity[i]","For each j: sum_i delivery[i,j] >= demand[j]","For each j: sum_i selected[i,j] >= min_contributors[j]","For each i,j: delivery[i,j] >= min_delivery[i]*selected[i,j]","For each i,j: delivery[i,j] <= capacity[i]*selected[i,j]"],"objective":"Minimize sum_i sum_j cost[i,j]*delivery[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 4)
    model.contracts = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.producers,
        initialize={i: params["capacity"][i] for i in model.producers},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize={j: params["demand"][j] for j in model.contracts},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.producers
            for j in model.contracts
        },
        within=pyo.Reals,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize={i: params["min_delivery"][i] for i in model.producers},
        within=pyo.NonNegativeReals,
    )
    model.min_contributors = pyo.Param(
        model.contracts,
        initialize={
            j: params["min_contributors"][j] for j in model.contracts
        },
        within=pyo.NonNegativeIntegers,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.selected = pyo.Var(
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

    model.demand_requirements = pyo.Constraint(
        model.contracts, rule=demand_rule
    )

    def contributors_rule(block, j):
        return (
            sum(block.selected[i, j] for i in block.producers)
            >= block.min_contributors[j]
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributors_rule
    )

    def minimum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            >= block.min_delivery[i] * block.selected[i, j]
        )

    model.minimum_delivery_links = pyo.Constraint(
        model.producers, model.contracts, rule=minimum_delivery_rule
    )

    def maximum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            <= block.capacity[i] * block.selected[i, j]
        )

    model.maximum_delivery_links = pyo.Constraint(
        model.producers, model.contracts, rule=maximum_delivery_rule
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}