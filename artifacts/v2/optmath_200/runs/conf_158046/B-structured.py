# IR: {"sets":{"I":"0..22"},"params":{"profit":"params['profit'][i], i in I","resource_coeff":"params['resource_coeff'][i], i in I","resource_total":"params['resource_total']","capacity":"params['capacity'][i], i in I"},"variables":{"production[i]":"NonNegativeReals, i in I"},"constraints":["sum(resource_coeff[i]*production[i] for i in I) <= resource_total","production[i] <= capacity[i], for each i in I"],"objective":"maximize sum(profit[i]*production[i] for i in I)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve with continuous production quantities; indexed inputs use indices 0..22."""
    model = pyo.ConcreteModel()
    model.items_set = pyo.RangeSet(0, 22)

    model.profit = pyo.Param(
        model.items_set,
        initialize={i: params["profit"][i] for i in model.items_set},
    )
    model.resource_coeff = pyo.Param(
        model.items_set,
        initialize={i: params["resource_coeff"][i] for i in model.items_set},
    )
    model.resource_total = pyo.Param(initialize=params["resource_total"])
    model.capacity = pyo.Param(
        model.items_set,
        initialize={i: params["capacity"][i] for i in model.items_set},
    )

    model.production = pyo.Var(
        model.items_set,
        domain=pyo.NonNegativeReals,
    )

    model.resource_limit = pyo.Constraint(
        expr=sum(
            model.resource_coeff[i] * model.production[i]
            for i in model.items_set
        )
        <= model.resource_total
    )

    def capacity_rule(block, i):
        return block.production[i] <= block.capacity[i]

    model.production_limits = pyo.Constraint(
        model.items_set,
        rule=capacity_rule,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[i] * model.production[i]
            for i in model.items_set
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}