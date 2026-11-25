import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = 6
    months = list(range(T))

    cum_A = params["cumulative_demand_A"]
    cum_B = params["cumulative_demand_B"]
    pc_A = params["production_cost_A"]
    pc_B = params["production_cost_B"]
    sc_A = params["setup_cost_A"]
    sc_B = params["setup_cost_B"]
    hc_A = params["holding_cost_A"]
    hc_B = params["holding_cost_B"]
    ru_A = params["resource_usage_A"]
    ru_B = params["resource_usage_B"]
    cap = params["resource_capacity"]

    # Per-month demand from cumulative demands (month 0 demand = cum[0])
    dem_A = [cum_A[0]] + [cum_A[t] - cum_A[t - 1] for t in range(1, T)]
    dem_B = [cum_B[0]] + [cum_B[t] - cum_B[t - 1] for t in range(1, T)]

    # Production upper bound by month (cumulative demand from that month onward)
    ub_A = {}
    ub_B = {}
    for t in months:
        ub_A[t] = cum_A[T - 1] - (cum_A[t - 1] if t > 0 else 0)
        ub_B[t] = cum_B[T - 1] - (cum_B[t - 1] if t > 0 else 0)

    total_A = cum_A[T - 1]
    total_B = cum_B[T - 1]
    bigM_A = total_A
    bigM_B = total_B

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=months)

    model.prod_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.prod_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup_A = pyo.Var(model.T, domain=pyo.Binary)
    model.setup_B = pyo.Var(model.T, domain=pyo.Binary)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(
            pc_A[t] * model.prod_A[t]
            + pc_B[t] * model.prod_B[t]
            + sc_A[t] * model.setup_A[t]
            + sc_B[t] * model.setup_B[t]
            + hc_A[t] * model.inv_A[t]
            + hc_B[t] * model.inv_B[t]
            for t in model.T
        ),
        sense=pyo.minimize,
    )

    # Inventory balance
    def inv_bal_A_rule(mdl, t):
        prev = mdl.inv_A[t - 1] if t > 0 else 0
        return mdl.inv_A[t] == prev + mdl.prod_A[t] - dem_A[t]

    def inv_bal_B_rule(mdl, t):
        prev = mdl.inv_B[t - 1] if t > 0 else 0
        return mdl.inv_B[t] == prev + mdl.prod_B[t] - dem_B[t]

    model.inv_bal_A = pyo.Constraint(model.T, rule=inv_bal_A_rule)
    model.inv_bal_B = pyo.Constraint(model.T, rule=inv_bal_B_rule)

    # No ending inventory
    model.end_inv_A = pyo.Constraint(expr=model.inv_A[T - 1] == 0)
    model.end_inv_B = pyo.Constraint(expr=model.inv_B[T - 1] == 0)

    # Production upper bounds (cumulative demand remaining)
    model.ub_A = pyo.Constraint(
        model.T, rule=lambda mdl, t: mdl.prod_A[t] <= ub_A[t]
    )
    model.ub_B = pyo.Constraint(
        model.T, rule=lambda mdl, t: mdl.prod_B[t] <= ub_B[t]
    )

    # Setup linking
    model.link_A = pyo.Constraint(
        model.T, rule=lambda mdl, t: mdl.prod_A[t] <= bigM_A * mdl.setup_A[t]
    )
    model.link_B = pyo.Constraint(
        model.T, rule=lambda mdl, t: mdl.prod_B[t] <= bigM_B * mdl.setup_B[t]
    )

    # Resource capacity
    model.res_cap = pyo.Constraint(
        model.T,
        rule=lambda mdl, t: ru_A * mdl.prod_A[t] + ru_B * mdl.prod_B[t] <= cap[t],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}