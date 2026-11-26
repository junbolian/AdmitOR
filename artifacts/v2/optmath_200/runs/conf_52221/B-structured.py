# IR: {
#   "sets": {"I": [0, 1, 2], "J": [0, 1, 2, 3, 4]},
#   "params": {
#     "producer_capacity": "nonnegative vector indexed by I",
#     "contract_demand": "nonnegative vector indexed by J",
#     "min_producers_per_contract": "nonnegative integer vector indexed by J",
#     "unit_cost": "cost matrix indexed by [i][j]",
#     "min_delivery_if_assigned": "nonnegative vector indexed by I"
#   },
#   "decision_variables": {
#     "delivery[i,j]": "nonnegative continuous, for i in I and j in J",
#     "assigned[i,j]": "binary, for i in I and j in J"
#   },
#   "constraints": [
#     "capacity_limits[i]: sum(delivery[i,j] for j in J) <= producer_capacity[i]",
#     "demand_requirements[j]: sum(delivery[i,j] for i in I) >= contract_demand[j]",
#     "producer_requirements[j]: sum(assigned[i,j] for i in I) >= min_producers_per_contract[j]",
#     "assignment_upper_bounds[i,j]: delivery[i,j] <= producer_capacity[i] * assigned[i,j]",
#     "assignment_lower_bounds[i,j]: delivery[i,j] >= min_delivery_if_assigned[i] * assigned[i,j]"
#   ],
#   "objective": "minimize sum(unit_cost[i,j] * delivery[i,j] for i in I and j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexable parameter vectors and a nested unit_cost matrix."""
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 2)
    model.J = pyo.RangeSet(0, 4)

    model.producer_capacity = pyo.Param(
        model.I,
        initialize={
            i: params["producer_capacity"][i]
            for i in model.I
        },
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.J,
        initialize={
            j: params["contract_demand"][j]
            for j in model.J
        },
        within=pyo.NonNegativeReals,
    )
    model.min_producers_per_contract = pyo.Param(
        model.J,
        initialize={
            j: params["min_producers_per_contract"][j]
            for j in model.J
        },
        within=pyo.NonNegativeIntegers,
    )
    model.unit_cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["unit_cost"][i][j]
            for i in model.I
            for j in model.J
        },
        within=pyo.Reals,
    )
    model.min_delivery_if_assigned = pyo.Param(
        model.I,
        initialize={
            i: params["min_delivery_if_assigned"][i]
            for i in model.I
        },
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )
    model.assigned = pyo.Var(
        model.I, model.J, domain=pyo.Binary
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.delivery[i, j] for j in instance.J)
            <= instance.producer_capacity[i]
        )

    model.capacity_limits = pyo.Constraint(
        model.I, rule=capacity_rule
    )

    def demand_rule(instance, j):
        return (
            sum(instance.delivery[i, j] for i in instance.I)
            >= instance.contract_demand[j]
        )

    model.demand_requirements = pyo.Constraint(
        model.J, rule=demand_rule
    )

    def producer_requirement_rule(instance, j):
        return (
            sum(instance.assigned[i, j] for i in instance.I)
            >= instance.min_producers_per_contract[j]
        )

    model.producer_requirements = pyo.Constraint(
        model.J, rule=producer_requirement_rule
    )

    def assignment_upper_rule(instance, i, j):
        return (
            instance.delivery[i, j]
            <= instance.producer_capacity[i] * instance.assigned[i, j]
        )

    model.assignment_upper_bounds = pyo.Constraint(
        model.I, model.J, rule=assignment_upper_rule
    )

    def assignment_lower_rule(instance, i, j):
        return (
            instance.delivery[i, j]
            >= instance.min_delivery_if_assigned[i] * instance.assigned[i, j]
        )

    model.assignment_lower_bounds = pyo.Constraint(
        model.I, model.J, rule=assignment_lower_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.delivery[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    # Appsi raises RuntimeError when it cannot load a feasible solution.
    # Leave success determination to objective evaluation below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}