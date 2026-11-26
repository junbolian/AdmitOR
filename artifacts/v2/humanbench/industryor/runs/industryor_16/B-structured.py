# IR: {"sets":{"Q":[0,1,2,3],"A":"{(i,j): i,j in Q, i<=j}","T":[0,1,2]},"params":{"storage_capacity":"params['storage_capacity']","storage_cost_a":"params['storage_cost_a']","storage_cost_b":"params['storage_cost_b']","buy_price":"params['buy_price'], indexed winter through autumn","sell_price":"params['sell_price'], indexed winter through autumn","max_sales":"params['max_sales'], indexed winter through autumn"},"variables":{"wood[i,j]":"continuous nonnegative; volume purchased in quarter i and sold in quarter j"},"constraints":["For each j in Q: sum(wood[i,j] for i<=j) <= max_sales[j].","For each t in T: sum(wood[i,j] for i<=t<j) <= storage_capacity.","Initial inventory is zero and autumn ending inventory is zero by the purchase-sale index structure."],"objective":{"sense":"maximize","expression":"sum((sell_price[j]-buy_price[i]-holding_cost(i,j))*wood[i,j] for (i,j) in A)","holding_cost":"0 if i=j; otherwise storage_cost_a+storage_cost_b*(j-i)"},"conventions":{"capacity":"Inventory carried between quarters.","storage_charge":"The stated a+b*u is the total per-volume charge for a cohort stored u quarters; same-quarter sales incur no storage charge."}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    storage_capacity = params["storage_capacity"]
    storage_cost_a = params["storage_cost_a"]
    storage_cost_b = params["storage_cost_b"]
    buy_price = params["buy_price"]
    sell_price = params["sell_price"]
    max_sales = params["max_sales"]

    model = pyo.ConcreteModel()

    model.quarters = pyo.Set(initialize=range(4), ordered=True)
    model.storage_boundaries = pyo.Set(initialize=range(3), ordered=True)
    model.purchase_sale_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (purchase_quarter, sale_quarter)
            for purchase_quarter in range(4)
            for sale_quarter in range(purchase_quarter, 4)
        ],
        ordered=True,
    )

    model.capacity_limit = pyo.Param(initialize=storage_capacity)
    model.storage_base_charge = pyo.Param(initialize=storage_cost_a)
    model.storage_duration_charge = pyo.Param(initialize=storage_cost_b)
    model.purchase_prices = pyo.Param(
        model.quarters,
        initialize={quarter: buy_price[quarter] for quarter in range(4)},
    )
    model.sale_prices = pyo.Param(
        model.quarters,
        initialize={quarter: sell_price[quarter] for quarter in range(4)},
    )
    model.sales_limits = pyo.Param(
        model.quarters,
        initialize={quarter: max_sales[quarter] for quarter in range(4)},
    )

    model.wood = pyo.Var(
        model.purchase_sale_pairs,
        domain=pyo.NonNegativeReals,
    )

    def sales_limit_rule(instance, sale_quarter):
        return (
            sum(
                instance.wood[purchase_quarter, sale_quarter]
                for purchase_quarter in range(sale_quarter + 1)
            )
            <= instance.sales_limits[sale_quarter]
        )

    model.quarterly_sales_limits = pyo.Constraint(
        model.quarters,
        rule=sales_limit_rule,
    )

    def storage_limit_rule(instance, boundary):
        return (
            sum(
                instance.wood[purchase_quarter, sale_quarter]
                for purchase_quarter, sale_quarter
                in instance.purchase_sale_pairs
                if purchase_quarter <= boundary < sale_quarter
            )
            <= instance.capacity_limit
        )

    model.quarterly_storage_limits = pyo.Constraint(
        model.storage_boundaries,
        rule=storage_limit_rule,
    )

    def holding_cost(instance, purchase_quarter, sale_quarter):
        if purchase_quarter == sale_quarter:
            return 0
        return (
            instance.storage_base_charge
            + instance.storage_duration_charge
            * (sale_quarter - purchase_quarter)
        )

    model.annual_profit = pyo.Objective(
        expr=sum(
            (
                model.sale_prices[sale_quarter]
                - model.purchase_prices[purchase_quarter]
                - holding_cost(model, purchase_quarter, sale_quarter)
            )
            * model.wood[purchase_quarter, sale_quarter]
            for purchase_quarter, sale_quarter
            in model.purchase_sale_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.annual_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}