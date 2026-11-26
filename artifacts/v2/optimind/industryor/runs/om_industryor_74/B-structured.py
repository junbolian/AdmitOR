# IR: {
#   "sets": {"Q": [0, 1, 2, 3], "A": "[(i,j) for i in Q for j in Q if i<=j]", "B": [0, 1, 2]},
#   "params": {
#     "purchase_price[Q]": "params['purchase_price']; 10000 yuan per 10000 m3",
#     "sale_price[Q]": "params['sale_price']; 10000 yuan per 10000 m3",
#     "max_sales[Q]": "params['max_sales']; 10000 m3",
#     "storage_capacity": "params['storage_capacity']; 10000 m3",
#     "storage_cost_a": "params['storage_cost_a']; yuan/m3",
#     "storage_cost_b": "params['storage_cost_b']; yuan/m3/quarter"
#   },
#   "variables": {"x[i,j]": "continuous nonnegative; timber purchased in i and sold in j, in 10000 m3"},
#   "definitions": {
#     "holding_cost[i,j]": "0 if i=j, else storage_cost_a+storage_cost_b*(j-i)",
#     "inventory[t]": "sum(x[i,j] for (i,j) in A if i<=t<j)"
#   },
#   "constraints": [
#     "For each j in Q: sum(x[i,j] for i in Q if i<=j)<=max_sales[j]",
#     "For each t in B: inventory[t]<=storage_capacity",
#     "Initial inventory is zero and all purchases are sold by autumn, enforced by A"
#   ],
#   "objective": "maximize sum((sale_price[j]-purchase_price[i]-holding_cost[i,j])*x[i,j] for (i,j) in A); 10000 yuan",
#   "assumptions": [
#     "Quarter order is Winter, Spring, Summer, Autumn",
#     "Capacity limits inventory carried between quarters",
#     "Same-quarter sales incur no storage charge; a is charged once per stored shipment"
#   ]
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.quarters = pyo.RangeSet(0, 3)
    model.boundaries = pyo.RangeSet(0, 2)
    model.shipment_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.quarters
            for j in model.quarters
            if i <= j
        ],
    )

    model.purchase_price = pyo.Param(
        model.quarters,
        initialize={q: params["purchase_price"][q] for q in model.quarters},
        within=pyo.Reals,
    )
    model.sale_price = pyo.Param(
        model.quarters,
        initialize={q: params["sale_price"][q] for q in model.quarters},
        within=pyo.Reals,
    )
    model.max_sales = pyo.Param(
        model.quarters,
        initialize={q: params["max_sales"][q] for q in model.quarters},
        within=pyo.NonNegativeReals,
    )
    model.storage_capacity = pyo.Param(
        initialize=params["storage_capacity"],
        within=pyo.NonNegativeReals,
    )
    model.storage_cost_a = pyo.Param(
        initialize=params["storage_cost_a"],
        within=pyo.NonNegativeReals,
    )
    model.storage_cost_b = pyo.Param(
        initialize=params["storage_cost_b"],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.shipment_pairs,
        domain=pyo.NonNegativeReals,
    )

    def holding_cost_rule(block, i, j):
        if i == j:
            return 0
        return block.storage_cost_a + block.storage_cost_b * (j - i)

    model.holding_cost = pyo.Expression(
        model.shipment_pairs,
        rule=holding_cost_rule,
    )

    def inventory_rule(block, t):
        return sum(
            block.x[i, j]
            for i, j in block.shipment_pairs
            if i <= t < j
        )

    model.inventory = pyo.Expression(
        model.boundaries,
        rule=inventory_rule,
    )

    def sales_limit_rule(block, j):
        return (
            sum(block.x[i, j] for i in block.quarters if i <= j)
            <= block.max_sales[j]
        )

    model.sales_limit = pyo.Constraint(
        model.quarters,
        rule=sales_limit_rule,
    )

    def capacity_limit_rule(block, t):
        return block.inventory[t] <= block.storage_capacity

    model.capacity_limit = pyo.Constraint(
        model.boundaries,
        rule=capacity_limit_rule,
    )

    # The volume and monetary units both contain a factor of 10000,
    # so the storage-cost coefficient requires no conversion factor.
    model.annual_profit = pyo.Objective(
        expr=sum(
            (
                model.sale_price[j]
                - model.purchase_price[i]
                - model.holding_cost[i, j]
            )
            * model.x[i, j]
            for i, j in model.shipment_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.annual_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}