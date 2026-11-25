# IR: {"sets":{"P":[0,1,2,3],"T":[0,1,2,3,4]},"params":{"profit_per_unit":"P-indexed","holding_cost_per_unit_period":"scalar","grinder_capacity":"T-indexed","drill_capacity":"T-indexed","borer_capacity":"T-indexed","max_inventory":"scalar","target_inventory_period4":"scalar","sales_limit_product0":"T-indexed","sales_limit_product1":"T-indexed","sales_limit_product2":"T-indexed","sales_limit_product3":"T-indexed","grinder_time":[1,1,2,2],"drill_time":2,"borer_time":1},"variables":{"production[P,T]":"continuous nonnegative","sales[P,T]":"continuous nonnegative","inventory[P,T]":"continuous nonnegative"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P,t in T with t>0","sum(grinder_time[p]*production[p,t] for p in P) <= grinder_capacity[t] for t in T","sum(drill_time*production[p,t] for p in P) <= drill_capacity[t] for t in T","sum(borer_time*production[p,t] for p in P) <= borer_capacity[t] for t in T","inventory[p,t] <= max_inventory for p in P,t in T","sales[p,t] <= sales_limit_product{p}[t] for p in P,t in T","inventory[p,4] = target_inventory_period4 for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost_per_unit_period*inventory[p,t] for p in P,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 3)
    model.T = pyo.RangeSet(0, 4)

    model.unit_profit = pyo.Param(
        model.P,
        initialize={p: params["profit_per_unit"][p] for p in model.P},
    )
    model.holding_cost = pyo.Param(
        initialize=params["holding_cost_per_unit_period"]
    )
    model.grinder_hours = pyo.Param(
        model.T,
        initialize={t: params["grinder_capacity"][t] for t in model.T},
    )
    model.drill_hours = pyo.Param(
        model.T,
        initialize={t: params["drill_capacity"][t] for t in model.T},
    )
    model.borer_hours = pyo.Param(
        model.T,
        initialize={t: params["borer_capacity"][t] for t in model.T},
    )
    model.inventory_capacity = pyo.Param(initialize=params["max_inventory"])
    model.final_inventory_target = pyo.Param(
        initialize=params["target_inventory_period4"]
    )

    sales_limits = (
        params["sales_limit_product0"],
        params["sales_limit_product1"],
        params["sales_limit_product2"],
        params["sales_limit_product3"],
    )
    model.sales_upper = pyo.Param(
        model.P,
        model.T,
        initialize={
            (p, t): sales_limits[p][t]
            for p in model.P
            for t in model.T
        },
    )
    model.grinder_time = pyo.Param(
        model.P, initialize={0: 1, 1: 1, 2: 2, 3: 2}
    )
    model.drill_time = pyo.Param(initialize=2)
    model.borer_time = pyo.Param(initialize=1)

    model.production = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def balance_rule(mod, p, t):
        if t == 0:
            return (
                mod.production[p, t]
                == mod.sales[p, t] + mod.inventory[p, t]
            )
        return (
            mod.inventory[p, t - 1] + mod.production[p, t]
            == mod.sales[p, t] + mod.inventory[p, t]
        )

    model.inventory_balance = pyo.Constraint(
        model.P, model.T, rule=balance_rule
    )
    model.grinder_capacity_constraint = pyo.Constraint(
        model.T,
        rule=lambda mod, t: sum(
            mod.grinder_time[p] * mod.production[p, t] for p in mod.P
        ) <= mod.grinder_hours[t],
    )
    model.drill_capacity_constraint = pyo.Constraint(
        model.T,
        rule=lambda mod, t: sum(
            mod.drill_time * mod.production[p, t] for p in mod.P
        ) <= mod.drill_hours[t],
    )
    model.borer_capacity_constraint = pyo.Constraint(
        model.T,
        rule=lambda mod, t: sum(
            mod.borer_time * mod.production[p, t] for p in mod.P
        ) <= mod.borer_hours[t],
    )
    model.inventory_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mod, p, t:
            mod.inventory[p, t] <= mod.inventory_capacity,
    )
    model.sales_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mod, p, t: mod.sales[p, t] <= mod.sales_upper[p, t],
    )
    model.ending_inventory = pyo.Constraint(
        model.P,
        rule=lambda mod, p:
            mod.inventory[p, 4] == mod.final_inventory_target,
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.unit_profit[p] * model.sales[p, t]
            - model.holding_cost * model.inventory[p, t]
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