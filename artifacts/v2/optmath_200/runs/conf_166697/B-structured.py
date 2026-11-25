# IR: {"sets":{"P":[0,1],"T":[0,1,2]},"params":["setup_cost","startup_cost","capacity","startup_time","holding_cost_P0","holding_cost_P1","backlog_cost_P0","backlog_cost_P1","demand_P0_P0","demand_P1_P0","demand_P0_P1","demand_P1_P1","demand_P0_P2","demand_P1_P2"],"variables":{"y[p,t]":"binary: product selected","z[p,t]":"binary: startup","x[p,t]":"nonnegative continuous: production","I[p,t]":"nonnegative continuous: ending inventory","B[p,t]":"nonnegative continuous: ending backlog"},"constraints":["I[p,t]-B[p,t]=(I[p,t-1]-B[p,t-1] if t>0 else 0)+x[p,t]-d[p,t]","sum_p y[p,t]<=1","x[p,t]<=capacity*y[p,t]","sum_p x[p,t]+startup_time*sum_p z[p,t]<=capacity","z[p,0]=y[p,0]","z[p,t]>=y[p,t]-y[p,t-1] for t>0","z[p,t]<=y[p,t] for t>0","z[p,t]<=1-y[p,t-1] for t>0"],"objective":"min sum_(p,t)(setup_cost*y[p,t]+startup_cost*z[p,t]+h[p]*I[p,t]+b[p]*B[p,t]); initial inventory and backlog zero; no terminal inventory or backlog restriction"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    setup_cost = params["setup_cost"]
    startup_cost = params["startup_cost"]
    capacity = params["capacity"]
    startup_time = params["startup_time"]

    holding_cost = {
        0: params["holding_cost_P0"],
        1: params["holding_cost_P1"],
    }
    backlog_cost = {
        0: params["backlog_cost_P0"],
        1: params["backlog_cost_P1"],
    }
    demand = {
        (0, 0): params["demand_P0_P0"],
        (1, 0): params["demand_P1_P0"],
        (0, 1): params["demand_P0_P1"],
        (1, 1): params["demand_P1_P1"],
        (0, 2): params["demand_P0_P2"],
        (1, 2): params["demand_P1_P2"],
    }

    model = pyo.ConcreteModel()
    model.products = pyo.Set(initialize=[0, 1], ordered=True)
    model.periods = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.later_periods = pyo.Set(initialize=[1, 2], ordered=True)

    model.y = pyo.Var(model.products, model.periods, domain=pyo.Binary)
    model.z = pyo.Var(model.products, model.periods, domain=pyo.Binary)
    model.x = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)
    model.I = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)
    model.B = pyo.Var(model.products, model.periods, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, product, period):
        previous_net_stock = (
            mdl.I[product, period - 1] - mdl.B[product, period - 1]
            if period > 0
            else 0
        )
        return (
            mdl.I[product, period] - mdl.B[product, period]
            == previous_net_stock
            + mdl.x[product, period]
            - demand[product, period]
        )

    model.material_balance = pyo.Constraint(
        model.products, model.periods, rule=balance_rule
    )
    model.single_product = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: sum(
            mdl.y[product, period] for product in mdl.products
        ) <= 1,
    )
    model.production_link = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda mdl, product, period: (
            mdl.x[product, period] <= capacity * mdl.y[product, period]
        ),
    )
    model.machine_capacity = pyo.Constraint(
        model.periods,
        rule=lambda mdl, period: (
            sum(mdl.x[product, period] for product in mdl.products)
            + startup_time
            * sum(mdl.z[product, period] for product in mdl.products)
            <= capacity
        ),
    )
    model.initial_startup = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: mdl.z[product, 0] == mdl.y[product, 0],
    )
    model.startup_lower = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=lambda mdl, product, period: (
            mdl.z[product, period]
            >= mdl.y[product, period] - mdl.y[product, period - 1]
        ),
    )
    model.startup_selected = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=lambda mdl, product, period: (
            mdl.z[product, period] <= mdl.y[product, period]
        ),
    )
    model.startup_previous = pyo.Constraint(
        model.products,
        model.later_periods,
        rule=lambda mdl, product, period: (
            mdl.z[product, period] <= 1 - mdl.y[product, period - 1]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            setup_cost * model.y[product, period]
            + startup_cost * model.z[product, period]
            + holding_cost[product] * model.I[product, period]
            + backlog_cost[product] * model.B[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}