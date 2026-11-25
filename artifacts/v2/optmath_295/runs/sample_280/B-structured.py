# IR: {"sets":{"F":"range(params['num_factories'])","T":"range(params['num_months'])"},"params":{"num_factories":"factory count","num_months":"month count","activation_cost":"indexed by F","production_cost":"indexed by F","min_production":"indexed by F","max_production":"indexed by F","demand":"indexed by T"},"variables":{"run[F,T]":"Binary","production[F,T]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for f in F, t in T","production[f,t] <= max_production[f] * run[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.Set(
        initialize=range(params["num_factories"]), ordered=True
    )
    model.T = pyo.Set(
        initialize=range(params["num_months"]), ordered=True
    )

    model.activation_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["activation_cost"][factory],
        within=pyo.Reals,
    )
    model.production_cost = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["production_cost"][factory],
        within=pyo.Reals,
    )
    model.min_production = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["min_production"][factory],
        within=pyo.Reals,
    )
    model.max_production = pyo.Param(
        model.F,
        initialize=lambda mdl, factory: params["max_production"][factory],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.T,
        initialize=lambda mdl, month: params["demand"][month],
        within=pyo.Reals,
    )

    model.run = pyo.Var(model.F, model.T, domain=pyo.Binary)
    model.production = pyo.Var(
        model.F, model.T, domain=pyo.NonNegativeReals
    )

    model.minimum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.run[factory, month]
        ),
    )
    model.maximum_output = pyo.Constraint(
        model.F,
        model.T,
        rule=lambda mdl, factory, month: (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.run[factory, month]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.T,
        rule=lambda mdl, month: (
            sum(mdl.production[factory, month] for factory in mdl.F)
            >= mdl.demand[month]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.activation_cost[factory] * model.run[factory, month]
            + model.production_cost[factory] * model.production[factory, month]
            for factory in model.F
            for month in model.T
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}