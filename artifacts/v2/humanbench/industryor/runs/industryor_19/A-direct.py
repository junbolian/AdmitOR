import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    t = {
        (1, 1): params["t_11"], (1, 2): params["t_12"], (1, 3): params["t_13"],
        (2, 1): params["t_21"], (2, 2): params["t_22"], (2, 3): params["t_23"],
        (3, 1): params["t_31"], (3, 2): params["t_32"], (3, 3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]

    model = pyo.ConcreteModel()

    # Start time of each product on each machine (flow shop, same order)
    model.start = pyo.Var(products, machines, within=pyo.NonNegativeReals)

    # Makespan (completion time of last product on last machine)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Each product must respect processing order across machines
    def machine_order_rule(mdl, i, j):
        if j == 1:
            return pyo.Constraint.Skip
        return mdl.start[i, j] >= mdl.start[i, j - 1] + t[(i, j - 1)]
    model.machine_order = pyo.Constraint(products, machines, rule=machine_order_rule)

    # Same product order on every machine: no overlap between consecutive products
    def product_order_rule(mdl, i, j):
        if i == 1:
            return pyo.Constraint.Skip
        return mdl.start[i, j] >= mdl.start[i - 1, j] + t[(i - 1, j)]
    model.product_order = pyo.Constraint(products, machines, rule=product_order_rule)

    # Makespan definition
    def makespan_rule(mdl, i):
        return mdl.makespan >= mdl.start[i, 3] + t[(i, 3)]
    model.makespan_def = pyo.Constraint(products, rule=makespan_rule)

    # Objective: minimize makespan
    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}