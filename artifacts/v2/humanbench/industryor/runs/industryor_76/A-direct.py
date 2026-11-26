import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_A = params["cost_A"]
    cost_B = params["cost_B"]
    cost_C = params["cost_C"]
    tpo_A = params["tables_per_order_A"]
    tpo_B = params["tables_per_order_B"]
    tpo_C = params["tables_per_order_C"]
    min_tables = params["min_tables"]
    max_tables = params["max_tables"]
    min_B_if_A = params["min_tables_B_if_A"]

    model = pyo.ConcreteModel()

    # Number of orders from each supplier (nonnegative integers)
    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xC = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Binary indicators for whether an order is placed
    model.yA = pyo.Var(domain=pyo.Binary)
    model.yB = pyo.Var(domain=pyo.Binary)
    model.yC = pyo.Var(domain=pyo.Binary)

    # Objective: minimize total cost
    model.total_cost = pyo.Objective(
        expr=cost_A * model.xA + cost_B * model.xB + cost_C * model.xC,
        sense=pyo.minimize,
    )

    # Total tables bounds
    model.min_tables_con = pyo.Constraint(
        expr=tpo_A * model.xA + tpo_B * model.xB + tpo_C * model.xC >= min_tables
    )
    model.max_tables_con = pyo.Constraint(
        expr=tpo_A * model.xA + tpo_B * model.xB + tpo_C * model.xC <= max_tables
    )

    # Link order counts to binaries
    model.link_A = pyo.Constraint(expr=model.xA <= max_tables * model.yA)
    model.link_B = pyo.Constraint(expr=model.xB <= max_tables * model.yB)
    model.link_C = pyo.Constraint(expr=model.xC <= max_tables * model.yC)

    # If order from A, must order at least min_B_if_A tables from B
    model.minB_if_A = pyo.Constraint(
        expr=tpo_B * model.xB >= min_B_if_A * model.yA
    )

    # If order from B, must also order from C
    model.B_implies_C = pyo.Constraint(expr=model.yB <= model.yC)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}