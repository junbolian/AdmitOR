# IR: {"sets":{"F":"range(params['num_factories'])","T":"range(params['num_months'])"},"params":{"num_factories":"factory count","num_months":"month count","activation_cost[f]":"fixed cost per active factory-month","production_cost[f]":"cost per unit","min_production[f]":"minimum output when active","max_production[f]":"maximum output when active","demand[t]":"monthly demand"},"variables":{"run[f,t]":"Binary","production[f,t]":"NonNegativeReals"},"constraints":["production[f,t] >= min_production[f] * run[f,t] for f in F, t in T","production[f,t] <= max_production[f] * run[f,t] for f in F, t in T","sum(production[f,t] for f in F) >= demand[t] for t in T"],"objective":"minimize sum(activation_cost[f]*run[f,t] + production_cost[f]*production[f,t] for f in F, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_factories = params["num_factories"]
    num_months = params["num_months"]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=range(num_factories), ordered=True)
    model.T = pyo.Set(initialize=range(num_months), ordered=True)

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

    def minimum_output_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            >= mdl.min_production[factory] * mdl.run[factory, month]
        )

    def maximum_output_rule(mdl, factory, month):
        return (
            mdl.production[factory, month]
            <= mdl.max_production[factory] * mdl.run[factory, month]
        )

    def demand_rule(mdl, month):
        return (
            sum(mdl.production[factory, month] for factory in mdl.F)
            >= mdl.demand[month]
        )

    model.minimum_output = pyo.Constraint(
        model.F, model.T, rule=minimum_output_rule
    )
    model.maximum_output = pyo.Constraint(
        model.F, model.T, rule=maximum_output_rule
    )
    model.demand_satisfaction = pyo.Constraint(
        model.T, rule=demand_rule
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective evaluation below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}