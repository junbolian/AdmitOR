# IR: {"sets":{"P":[0,1,2],"T":[0,1,2,3,4]},"params":{"profit_per_unit":"P-indexed","holding_cost":"scalar","machine_hours_grinders":"T-indexed","machine_hours_drills":"T-indexed","machine_hours_borers":"T-indexed","time_req_grinders":"P-indexed","time_req_drills":"P-indexed","time_req_borers":"P-indexed","inventory_capacity":"scalar","sales_limit_p0":"T-indexed","sales_limit_p1":"T-indexed","sales_limit_p2":"T-indexed","target_inventory":"scalar"},"variables":{"production[P,T]":"nonnegative continuous","sales[P,T]":"nonnegative continuous","inventory[P,T]":"nonnegative continuous"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P,t in T with t>0","sum(time_req_grinders[p]*production[p,t] for p in P) <= machine_hours_grinders[t] for t in T","sum(time_req_drills[p]*production[p,t] for p in P) <= machine_hours_drills[t] for t in T","sum(time_req_borers[p]*production[p,t] for p in P) <= machine_hours_borers[t] for t in T","inventory[p,t] <= inventory_capacity for p in P,t in T","sales[0,t] <= sales_limit_p0[t] for t in T","sales[1,t] <= sales_limit_p1[t] for t in T","sales[2,t] <= sales_limit_p2[t] for t in T","inventory[p,4] = target_inventory for p in P"],"objective":"maximize sum(profit_per_unit[p]*sales[p,t] - holding_cost*inventory[p,t] for p in P,t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 2)
    model.T = pyo.RangeSet(0, 4)

    model.profit_per_unit = pyo.Param(
        model.P,
        initialize=lambda mdl, product: params["profit_per_unit"][product],
    )
    model.holding_cost = pyo.Param(initialize=params["holding_cost"])
    model.inventory_capacity = pyo.Param(
        initialize=params["inventory_capacity"]
    )
    model.target_inventory = pyo.Param(
        initialize=params["target_inventory"]
    )

    model.machine_hours_grinders = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["machine_hours_grinders"][period],
    )
    model.machine_hours_drills = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["machine_hours_drills"][period],
    )
    model.machine_hours_borers = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["machine_hours_borers"][period],
    )

    model.time_req_grinders = pyo.Param(
        model.P,
        initialize=lambda mdl, product: params["time_req_grinders"][product],
    )
    model.time_req_drills = pyo.Param(
        model.P,
        initialize=lambda mdl, product: params["time_req_drills"][product],
    )
    model.time_req_borers = pyo.Param(
        model.P,
        initialize=lambda mdl, product: params["time_req_borers"][product],
    )

    model.sales_limit_p0 = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["sales_limit_p0"][period],
    )
    model.sales_limit_p1 = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["sales_limit_p1"][period],
    )
    model.sales_limit_p2 = pyo.Param(
        model.T,
        initialize=lambda mdl, period: params["sales_limit_p2"][period],
    )

    model.production = pyo.Var(
        model.P, model.T, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.P, model.T, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.P, model.T, domain=pyo.NonNegativeReals
    )

    def initial_balance_rule(mdl, product):
        return (
            mdl.production[product, 0]
            == mdl.sales[product, 0] + mdl.inventory[product, 0]
        )

    model.initial_balance = pyo.Constraint(
        model.P, rule=initial_balance_rule
    )

    def inventory_balance_rule(mdl, product, period):
        if period == 0:
            return pyo.Constraint.Skip
        return (
            mdl.inventory[product, period - 1]
            + mdl.production[product, period]
            == mdl.sales[product, period] + mdl.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.P, model.T, rule=inventory_balance_rule
    )

    def grinder_capacity_rule(mdl, period):
        return (
            sum(
                mdl.time_req_grinders[product]
                * mdl.production[product, period]
                for product in mdl.P
            )
            <= mdl.machine_hours_grinders[period]
        )

    model.grinder_capacity = pyo.Constraint(
        model.T, rule=grinder_capacity_rule
    )

    def drill_capacity_rule(mdl, period):
        return (
            sum(
                mdl.time_req_drills[product]
                * mdl.production[product, period]
                for product in mdl.P
            )
            <= mdl.machine_hours_drills[period]
        )

    model.drill_capacity = pyo.Constraint(
        model.T, rule=drill_capacity_rule
    )

    def borer_capacity_rule(mdl, period):
        return (
            sum(
                mdl.time_req_borers[product]
                * mdl.production[product, period]
                for product in mdl.P
            )
            <= mdl.machine_hours_borers[period]
        )

    model.borer_capacity = pyo.Constraint(
        model.T, rule=borer_capacity_rule
    )

    model.inventory_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, product, period: (
            mdl.inventory[product, period] <= mdl.inventory_capacity
        ),
    )

    model.sales_cap_p0 = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            mdl.sales[0, period] <= mdl.sales_limit_p0[period]
        ),
    )
    model.sales_cap_p1 = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            mdl.sales[1, period] <= mdl.sales_limit_p1[period]
        ),
    )
    model.sales_cap_p2 = pyo.Constraint(
        model.T,
        rule=lambda mdl, period: (
            mdl.sales[2, period] <= mdl.sales_limit_p2[period]
        ),
    )

    model.terminal_inventory = pyo.Constraint(
        model.P,
        rule=lambda mdl, product: (
            mdl.inventory[product, 4] == mdl.target_inventory
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit_per_unit[product] * model.sales[product, period]
            - model.holding_cost * model.inventory[product, period]
            for product in model.P
            for period in model.T
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_profit))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}