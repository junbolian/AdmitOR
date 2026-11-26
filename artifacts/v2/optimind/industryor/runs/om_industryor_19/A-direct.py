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
    min_tables_B_if_A = params["min_tables_B_if_A"]

    model = pyo.ConcreteModel()

    # Integer number of orders from each supplier
    model.orders_A = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.orders_B = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.orders_C = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Binary indicators for placing orders
    model.use_A = pyo.Var(domain=pyo.Binary)
    model.use_B = pyo.Var(domain=pyo.Binary)

    # Total tables
    model.total_tables = pyo.Expression(
        expr=tpo_A * model.orders_A + tpo_B * model.orders_B + tpo_C * model.orders_C
    )

    # Objective: minimize total cost
    model.total_cost = pyo.Objective(
        expr=cost_A * model.orders_A + cost_B * model.orders_B + cost_C * model.orders_C,
        sense=pyo.minimize,
    )

    # Table bounds
    model.min_tables_con = pyo.Constraint(expr=model.total_tables >= min_tables)
    model.max_tables_con = pyo.Constraint(expr=model.total_tables <= max_tables)

    # Indicator linking: orders > 0 implies use binary
    model.link_A = pyo.Constraint(expr=model.orders_A <= pyo.ceil(max_tables / tpo_A) * model.use_A)
    model.link_B = pyo.Constraint(expr=model.orders_B <= pyo.ceil(max_tables / tpo_B) * model.use_B)

    # If A is used, at least min_tables_B_if_A tables from B
    model.A_requires_B_con = pyo.Constraint(
        expr=tpo_B * model.orders_B >= min_tables_B_if_A * model.use_A
    )

    # If B is used, must also order from C
    model.B_requires_C_con = pyo.Constraint(expr=model.use_B <= model.orders_C)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}