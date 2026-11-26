import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    unit_cost = params["unit_cost"]
    p1_target = params["full_satisfaction_target_customer4"]
    p5_balance = params["balance_satisfaction_target_customers1and3"]
    p2_min_rate = params["remaining_customers_min_satisfaction_rate"]
    p3_min_f31 = params["factory3_to_customer1_min"]
    p4_weight = params["factory2_to_customer4_penalty_weight"]

    nF = int(params["num_factories"])
    nC = int(params["num_customers"])

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(1, nF)
    model.C = pyo.RangeSet(1, nC)

    model.x = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    # p6: transportation cost
    model.cost = pyo.Expression(
        expr=sum(unit_cost[i - 1][j - 1] * model.x[i, j]
                 for i in model.F for j in model.C)
    )

    # p4: penalty discouraging factory 2 -> customer 4
    model.penalty = pyo.Expression(expr=p4_weight * model.x[2, 4])

    model.obj = pyo.Objective(expr=model.cost + model.penalty, sense=pyo.minimize)

    # supply capacity
    model.supply_con = pyo.Constraint(
        model.F,
        rule=lambda m, i: sum(m.x[i, j] for j in m.C) <= supply[i - 1]
    )

    # shipments cannot exceed customer demand
    model.demand_cap = pyo.Constraint(
        model.F, model.C,
        rule=lambda m, i, j: m.x[i, j] <= demand[j - 1]
    )

    # p1: customer 4 fully satisfied
    model.p1 = pyo.Constraint(
        expr=sum(model.x[i, 4] for i in model.F) == p1_target)

    # p2: remaining customers (1,2,3) satisfaction >= min rate
    model.p2 = pyo.Constraint(
        model.F, model.C,
        rule=lambda m, i, j: (m.x[i, j] <= p2_min_rate * demand[j - 1])
        if j in (1, 2, 3) else pyo.Constraint.Skip
    )
    model.p2b = pyo.Constraint(
        [1, 2, 3],
        rule=lambda m, j: sum(m.x[i, j] for i in m.F)
        >= p2_min_rate * demand[j - 1]
    )

    # p3: factory 3 -> customer 1 at least given amount
    model.p3 = pyo.Constraint(expr=model.x[3, 1] >= p3_min_f31)

    # p5: balance satisfaction degrees of customers 1 and 3 (soft, penalized)
    model.d1 = pyo.Expression(
        expr=sum(model.x[i, 1] for i in model.F) / demand[0])
    model.d3 = pyo.Expression(
        expr=sum(model.x[i, 3] for i in model.F) / demand[2])
    model.dev_pos = pyo.Var(domain=pyo.NonNegativeReals)
    model.dev_neg = pyo.Var(domain=pyo.NonNegativeReals)
    model.p5 = pyo.Constraint(
        expr=model.d1 - p5_balance * model.d3
        == model.dev_pos - model.dev_neg)
    model.obj.deactivate()
    model.obj_combined = pyo.Objective(
        expr=model.cost + model.penalty + model.dev_pos + model.dev_neg,
        sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj_combined))

    return {"objective": obj_val, "status": "optimal"}