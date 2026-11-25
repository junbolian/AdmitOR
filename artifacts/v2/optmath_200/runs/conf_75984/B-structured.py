# IR: {"sets":{"F":[0,1,2,3],"T":[0,1,2,3]},"params":{"fixed_cost":"F -> real","variable_cost":"F -> real","min_production":"F -> real","max_production":"F -> real","demand":"T -> real"},"variables":{"run[f,t]":"binary, f in F, t in T","production[f,t]":"nonnegative continuous, f in F, t in T"},"constraints":["production[f,t] >= min_production[f]*run[f,t], forall f,t","production[f,t] <= max_production[f]*run[f,t], forall f,t","sum(production[f,t] for f in F) >= demand[t], forall t"],"objective":"minimize sum(fixed_cost[f]*run[f,t] + variable_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using factory-indexed cost/capacity data and month-indexed demand."""
    model = pyo.ConcreteModel()

    model.factories = pyo.RangeSet(0, 3)
    model.months = pyo.RangeSet(0, 3)

    model.fixed_cost = pyo.Param(
        model.factories,
        initialize={f: params["fixed_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.factories,
        initialize={f: params["variable_cost"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.factories,
        initialize={f: params["min_production"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.factories,
        initialize={f: params["max_production"][f] for f in model.factories},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.months,
        initialize={t: params["demand"][t] for t in model.months},
        within=pyo.Reals,
    )

    model.run = pyo.Var(
        model.factories, model.months, domain=pyo.Binary
    )
    model.production = pyo.Var(
        model.factories, model.months, domain=pyo.NonNegativeReals
    )

    def minimum_production_rule(problem, f, t):
        return (
            problem.production[f, t]
            >= problem.min_production[f] * problem.run[f, t]
        )

    model.minimum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=minimum_production_rule
    )

    def maximum_production_rule(problem, f, t):
        return (
            problem.production[f, t]
            <= problem.max_production[f] * problem.run[f, t]
        )

    model.maximum_production_constraint = pyo.Constraint(
        model.factories, model.months, rule=maximum_production_rule
    )

    def demand_rule(problem, t):
        return (
            sum(problem.production[f, t] for f in problem.factories)
            >= problem.demand[t]
        )

    model.demand_constraint = pyo.Constraint(
        model.months, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.run[f, t]
            + model.variable_cost[f] * model.production[f, t]
            for f in model.factories
            for t in model.months
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}