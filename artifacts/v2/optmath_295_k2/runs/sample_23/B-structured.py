# IR: {"sets":{"A":[0,1,2,3,4,5],"R":[0,1,2,3]},"params":{"availability":"availability[a] from params","demand":"demand[r] from params","capability":"capability[a,r] from params","cost":"cost[a,r] from params"},"variables":{"x[a,r]":"nonnegative integer"},"constraints":["forall a in A: sum(x[a,r] for r in R) <= availability[a]","forall r in R: sum(capability[a,r]*x[a,r] for a in A) >= demand[r]"],"objective":"minimize sum(cost[a,r]*x[a,r] for a in A for r in R)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, position, prefix):
    """Accept sequences or mappings keyed by labels or integer indices."""
    if isinstance(data, Mapping):
        label = f"{prefix}_{position}"
        return data[label] if label in data else data[position]
    return data[position]


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.A = pyo.RangeSet(0, 5)
    model.R = pyo.RangeSet(0, 3)

    model.availability = pyo.Param(
        model.A,
        initialize={
            a: _entry(availability, a, "aircraft")
            for a in model.A
        },
    )
    model.demand = pyo.Param(
        model.R,
        initialize={
            r: _entry(demand, r, "route")
            for r in model.R
        },
    )
    model.capability = pyo.Param(
        model.A,
        model.R,
        initialize={
            (a, r): _entry(_entry(capability, a, "aircraft"), r, "route")
            for a in model.A
            for r in model.R
        },
    )
    model.cost = pyo.Param(
        model.A,
        model.R,
        initialize={
            (a, r): _entry(_entry(cost, a, "aircraft"), r, "route")
            for a in model.A
            for r in model.R
        },
    )

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(instance, a):
        return (
            sum(instance.x[a, r] for r in instance.R)
            <= instance.availability[a]
        )

    def demand_rule(instance, r):
        return (
            sum(
                instance.capability[a, r] * instance.x[a, r]
                for a in instance.A
            )
            >= instance.demand[r]
        )

    model.availability_limits = pyo.Constraint(
        model.A, rule=availability_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.R, rule=demand_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[a, r] * model.x[a, r]
            for a in model.A
            for r in model.R
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}