# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4,5]},"params":{"profit_per_unit":"P","holding_cost_per_unit_per_period":"scalar","grinder_hours_per_unit":"P","drill_hours_per_unit":"P","borer_hours_per_unit":"P","grinder_capacity_per_period":"T","drill_capacity_per_period":"T","borer_capacity_per_period":"T","max_inventory_per_product":"scalar","max_sales":"P x T","final_inventory_target":"scalar"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["production[p,0] - sales[p,0] - inventory[p,0] = 0 for p in P","inventory[p,t-1] + production[p,t] - sales[p,t] - inventory[p,t] = 0 for p in P, t > 0","sum_p grinder_hours_per_unit[p]*production[p,t] <= grinder_capacity_per_period[t] for t in T","sum_p drill_hours_per_unit[p]*production[p,t] <= drill_capacity_per_period[t] for t in T","sum_p borer_hours_per_unit[p]*production[p,t] <= borer_capacity_per_period[t] for t in T","inventory[p,t] <= max_inventory_per_product for p in P, t in T","sales[p,t] <= max_sales[p,t] for p in P, t in T","inventory[p,5] = final_inventory_target for p in P"],"objective":"maximize sum_{p,t}(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_per_period*inventory[p,t])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 5)

    model.profit_per_unit = pyo.Param(
        model.P,
        initialize=lambda mdl, p: float(params["profit_per_unit"][p]),
    )
    model.holding_cost_per_unit_per_period = pyo.Param(
        initialize=float(params["holding_cost_per_unit_per_period"])
    )
    model.grinder_hours_per_unit = pyo.Param(
        model.P,
        initialize=lambda mdl, p: float(params["grinder_hours_per_unit"][p]),
    )
    model.drill_hours_per_unit = pyo.Param(
        model.P,
        initialize=lambda mdl, p: float(params["drill_hours_per_unit"][p]),
    )
    model.borer_hours_per_unit = pyo.Param(
        model.P,
        initialize=lambda mdl, p: float(params["borer_hours_per_unit"][p]),
    )
    model.grinder_capacity_per_period = pyo.Param(
        model.T,
        initialize=lambda mdl, t: float(
            params["grinder_capacity_per_period"][t]
        ),
    )
    model.drill_capacity_per_period = pyo.Param(
        model.T,
        initialize=lambda mdl, t: float(
            params["drill_capacity_per_period"][t]
        ),
    )
    model.borer_capacity_per_period = pyo.Param(
        model.T,
        initialize=lambda mdl, t: float(
            params["borer_capacity_per_period"][t]
        ),
    )
    model.max_inventory_per_product = pyo.Param(
        initialize=float(params["max_inventory_per_product"])
    )
    model.max_sales = pyo.Param(
        model.P,
        model.T,
        initialize=lambda mdl, p, t: float(params["max_sales"][p][t]),
    )
    model.final_inventory_target = pyo.Param(
        initialize=float(params["final_inventory_target"])
    )

    model.production = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    # Tuple-form constraints avoid evaluating constant relations as booleans.
    def inventory_balance_rule(mdl, p, t):
        balance = (
            mdl.production[p, t]
            - mdl.sales[p, t]
            - mdl.inventory[p, t]
        )
        if t > 0:
            balance += mdl.inventory[p, t - 1]
        return (0, balance, 0)

    model.inventory_balance = pyo.Constraint(
        model.P, model.T, rule=inventory_balance_rule
    )

    model.grinder_capacity = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            None,
            sum(
                mdl.grinder_hours_per_unit[p] * mdl.production[p, t]
                for p in mdl.P
            ),
            mdl.grinder_capacity_per_period[t],
        ),
    )
    model.drill_capacity = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            None,
            sum(
                mdl.drill_hours_per_unit[p] * mdl.production[p, t]
                for p in mdl.P
            ),
            mdl.drill_capacity_per_period[t],
        ),
    )
    model.borer_capacity = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: (
            None,
            sum(
                mdl.borer_hours_per_unit[p] * mdl.production[p, t]
                for p in mdl.P
            ),
            mdl.borer_capacity_per_period[t],
        ),
    )
    model.inventory_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, p, t: (
            None,
            mdl.inventory[p, t],
            mdl.max_inventory_per_product,
        ),
    )
    model.sales_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, p, t: (
            None,
            mdl.sales[p, t],
            mdl.max_sales[p, t],
        ),
    )
    model.ending_inventory = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: (
            mdl.final_inventory_target,
            mdl.inventory[p, 5],
            mdl.final_inventory_target,
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[p] * model.sales[p, t]
            - model.holding_cost_per_unit_per_period * model.inventory[p, t]
            for p in model.P
            for t in model.T
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