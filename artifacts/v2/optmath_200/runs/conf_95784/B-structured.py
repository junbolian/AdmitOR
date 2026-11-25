# IR: {"sets":{"P":[0,1],"T":[0,1,2,3],"R":["grinder","drill","borer"]},"params":{"profit0":"scalar","profit1":"scalar","hold_cost0":"scalar","hold_cost1":"scalar","inv_cap":"scalar","sales_max0":"indexed by T","sales_max1":"indexed by T","grinder_hours0":"scalar","grinder_hours1":"scalar","grinder_cap":"indexed by T, including maintenance","drill_hours0":"scalar","drill_hours1":"scalar","drill_cap":"indexed by T","borer_hours0":"scalar","borer_hours1":"scalar","borer_cap":"indexed by T","final_inv_target":"scalar"},"parameter_mappings":{"profit[p]":"[profit0,profit1][p]","holding_cost[p]":"[hold_cost0,hold_cost1][p]","sales_limit[p,t]":"[sales_max0,sales_max1][p][t]","hours[r,p]":"params[r+'_hours'+str(p)]","capacity[r,t]":"params[r+'_cap'][t]"},"variables":{"production[p,t]":"NonNegativeReals","sales[p,t]":"NonNegativeReals","inventory[p,t]":"NonNegativeReals"},"constraints":["production[p,0] = sales[p,0] + inventory[p,0] for p in P","inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t] for p in P, t in T with t>0","inventory[p,t] <= inv_cap for p in P, t in T","sales[p,t] <= sales_limit[p,t] for p in P, t in T","sum(hours[r,p]*production[p,t] for p in P) <= capacity[r,t] for r in R, t in T","inventory[p,3] = final_inv_target for p in P"],"objective":"maximize sum(profit[p]*sales[p,t] - holding_cost[p]*inventory[p,t] for p in P, t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Period-indexed inputs must support integer indexing for periods 0–3."""
    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 1)
    model.periods = pyo.RangeSet(0, 3)
    model.resources = pyo.Set(
        initialize=["grinder", "drill", "borer"], ordered=True
    )

    model.profit = pyo.Param(
        model.products,
        initialize={0: params["profit0"], 1: params["profit1"]},
    )
    model.holding_cost = pyo.Param(
        model.products,
        initialize={0: params["hold_cost0"], 1: params["hold_cost1"]},
    )
    model.inventory_limit = pyo.Param(initialize=params["inv_cap"])
    model.terminal_target = pyo.Param(initialize=params["final_inv_target"])

    sales_limits = {
        0: params["sales_max0"],
        1: params["sales_max1"],
    }
    model.sales_limit = pyo.Param(
        model.products,
        model.periods,
        initialize={
            (product, period): sales_limits[product][period]
            for product in model.products
            for period in model.periods
        },
    )

    hours = {
        ("grinder", 0): params["grinder_hours0"],
        ("grinder", 1): params["grinder_hours1"],
        ("drill", 0): params["drill_hours0"],
        ("drill", 1): params["drill_hours1"],
        ("borer", 0): params["borer_hours0"],
        ("borer", 1): params["borer_hours1"],
    }
    model.hours = pyo.Param(
        model.resources, model.products, initialize=hours
    )

    capacities = {
        "grinder": params["grinder_cap"],
        "drill": params["drill_cap"],
        "borer": params["borer_cap"],
    }
    model.capacity = pyo.Param(
        model.resources,
        model.periods,
        initialize={
            (resource, period): capacities[resource][period]
            for resource in model.resources
            for period in model.periods
        },
    )

    model.production = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.sales = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.periods, domain=pyo.NonNegativeReals
    )

    def inventory_balance_rule(instance, product, period):
        if period == 0:
            return (
                instance.production[product, period]
                == instance.sales[product, period]
                + instance.inventory[product, period]
            )
        return (
            instance.inventory[product, period - 1]
            + instance.production[product, period]
            == instance.sales[product, period]
            + instance.inventory[product, period]
        )

    model.inventory_balance = pyo.Constraint(
        model.products, model.periods, rule=inventory_balance_rule
    )

    model.inventory_capacity = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.inventory[product, period] <= instance.inventory_limit
        ),
    )

    model.sales_capacity = pyo.Constraint(
        model.products,
        model.periods,
        rule=lambda instance, product, period: (
            instance.sales[product, period]
            <= instance.sales_limit[product, period]
        ),
    )

    model.machine_capacity = pyo.Constraint(
        model.resources,
        model.periods,
        rule=lambda instance, resource, period: (
            sum(
                instance.hours[resource, product]
                * instance.production[product, period]
                for product in instance.products
            )
            <= instance.capacity[resource, period]
        ),
    )

    model.final_inventory = pyo.Constraint(
        model.products,
        rule=lambda instance, product: (
            instance.inventory[product, 3] == instance.terminal_target
        ),
    )

    model.total_profit = pyo.Objective(
        expr=sum(
            model.profit[product] * model.sales[product, period]
            - model.holding_cost[product] * model.inventory[product, period]
            for product in model.products
            for period in model.periods
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_profit))
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}