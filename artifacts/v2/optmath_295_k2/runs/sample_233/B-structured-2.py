# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"cost":"real[P,C]","capacity":"nonnegative_real[P]","demand":"nonnegative_real[C]","min_producers":"nonnegative_integer[C]","min_delivery":"nonnegative_real[P]"},"variables":{"delivery[P,C]":"nonnegative_real","assigned[P,C]":"binary"},"constraints":["For each i: sum_j delivery[i,j] <= capacity[i]","For each j: sum_i delivery[i,j] >= demand[j]","For each j: sum_i assigned[i,j] >= min_producers[j]","For each i,j: delivery[i,j] >= min_delivery[i]*assigned[i,j]","For each i,j: delivery[i,j] <= capacity[i]*assigned[i,j]"],"objective":"minimize sum_i sum_j cost[i,j]*delivery[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept cost as a nested array/mapping and other inputs as indexed vectors."""
    model = pyo.ConcreteModel()

    model.producers = pyo.RangeSet(0, 3)
    model.contracts = pyo.RangeSet(0, 4)

    model.cost = pyo.Param(
        model.producers,
        model.contracts,
        initialize=lambda _, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.producers,
        initialize=lambda _, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.contracts,
        initialize=lambda _, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.min_producers = pyo.Param(
        model.contracts,
        initialize=lambda _, j: params["min_producers"][j],
        within=pyo.NonNegativeIntegers,
    )
    model.min_delivery = pyo.Param(
        model.producers,
        initialize=lambda _, i: params["min_delivery"][i],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.producers, model.contracts, domain=pyo.NonNegativeReals
    )
    model.assigned = pyo.Var(
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

    def contributor_rule(block, j):
        return (
            sum(block.assigned[i, j] for i in block.producers)
            >= block.min_producers[j]
        )

    model.contributor_requirements = pyo.Constraint(
        model.contracts, rule=contributor_rule
    )

    def minimum_delivery_rule(block, i, j):
        return (
            block.delivery[i, j]
            >= block.min_delivery[i] * block.assigned[i, j]
        )

    model.assignment_minimums = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=minimum_delivery_rule,
    )

    def assignment_upper_rule(block, i, j):
        return (
            block.delivery[i, j]
            <= block.capacity[i] * block.assigned[i, j]
        )

    model.assignment_upper_bounds = pyo.Constraint(
        model.producers,
        model.contracts,
        rule=assignment_upper_rule,
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
        # APPsi raises this when its default solution loading finds no solution.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}