# IR: {"sets":{"markets":[0,1,2,3,4]},"params":{"demand":"required quantity indexed by market","profit_margin":"unit profit indexed by market"},"variables":{"supply":{"index":"markets","type":"nonnegative continuous"}},"constraints":["supply[i] == demand[i] for each i in markets"],"objective":{"sense":"maximize","expression":"sum(profit_margin[i] * supply[i] for i in markets)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.markets = pyo.RangeSet(0, 4)

    model.demand = pyo.Param(
        model.markets,
        initialize={i: params["demand"][i] for i in model.markets},
        within=pyo.Reals,
    )
    model.profit_margin = pyo.Param(
        model.markets,
        initialize={i: params["profit_margin"][i] for i in model.markets},
        within=pyo.Reals,
    )

    model.supply = pyo.Var(model.markets, domain=pyo.NonNegativeReals)

    def demand_rule(instance, i):
        return instance.supply[i] == instance.demand[i]

    model.demand_satisfaction = pyo.Constraint(
        model.markets, rule=demand_rule
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_margin[i] * model.supply[i]
            for i in model.markets
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}