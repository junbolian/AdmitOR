import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_capacity = params["warehouse_capacity"]
    initial_inventory = params["initial_inventory"]
    purchase_price = params["purchase_price"]
    selling_price = params["selling_price"]

    months = [1, 2, 3]

    model = pyo.ConcreteModel()

    model.months = pyo.Set(initialize=months)

    # Decision variables: units purchased and sold each month
    model.purchase = pyo.Var(model.months, within=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.months, within=pyo.NonNegativeReals)
    # Inventory carried at end of each month
    model.inventory = pyo.Var(model.months, within=pyo.NonNegativeReals,
                              bounds=(0, warehouse_capacity))

    # Objective: total profit (sales revenue - purchase cost)
    def obj_rule(mdl):
        return sum(selling_price[i - 1] * mdl.sale[i]
                   for i in mdl.months) - \
               sum(purchase_price[i - 1] * mdl.purchase[i]
                   for i in mdl.months)
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance constraints
    model.balance = pyo.ConstraintList()
    for i in months:
        prev_inv = initial_inventory if i == 1 else model.inventory[i - 1]
        model.balance.add(
            model.inventory[i] == prev_inv + model.purchase[i] - model.sale[i]
        )

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))

    return {"objective": obj_val, "status": "optimal"}