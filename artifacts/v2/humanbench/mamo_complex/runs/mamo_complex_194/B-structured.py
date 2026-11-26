# IR: {"sets":{"products":[1,2],"repair_cases":[0,1]},"params":["machine_hours_per_unit_p1","machine_hours_per_unit_p2","machine_hours_available","production_cost_p1","production_cost_p2","selling_price_p1","selling_price_p2","available_cash","revenue_advance_rate_p1","revenue_advance_rate_p2","extra_machine_hours","repair_cost"],"variables":{"weight[r]":"continuous nonnegative","production[i,r]":"continuous nonnegative"},"constraints":["sum_r weight[r] = 1","for each r: sum_i hours[i]*production[i,r] <= (machine_hours_available+r*extra_machine_hours)*weight[r]","for each r: sum_i (cost[i]-advance[i]*price[i])*production[i,r] <= (available_cash-r*repair_cost)*weight[r]"],"objective":"maximize sum_i,r (price[i]-cost[i])*production[i,r]-repair_cost*weight[1]","output":"optimal objective rounded to the nearest dollar"}
#
# Repair case 0 means no repairs; case 1 means purchasing all repairs.
# This disaggregated LP represents the convex hull of those two cases.
# Its maximum equals the better feasible case, so repairs retain their
# all-or-nothing meaning without requiring an integer variable.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=[1, 2], ordered=True)
    model.repair_cases = pyo.Set(initialize=[0, 1], ordered=True)

    model.hours = pyo.Param(
        model.products,
        initialize={
            1: params["machine_hours_per_unit_p1"],
            2: params["machine_hours_per_unit_p2"],
        },
        within=pyo.PositiveReals,
    )
    model.production_cost = pyo.Param(
        model.products,
        initialize={
            1: params["production_cost_p1"],
            2: params["production_cost_p2"],
        },
    )
    model.selling_price = pyo.Param(
        model.products,
        initialize={
            1: params["selling_price_p1"],
            2: params["selling_price_p2"],
        },
    )
    model.advance_rate = pyo.Param(
        model.products,
        initialize={
            1: params["revenue_advance_rate_p1"],
            2: params["revenue_advance_rate_p2"],
        },
    )
    model.machine_hours_available = pyo.Param(
        initialize=params["machine_hours_available"]
    )
    model.available_cash = pyo.Param(initialize=params["available_cash"])
    model.extra_machine_hours = pyo.Param(
        initialize=params["extra_machine_hours"]
    )
    model.repair_cost = pyo.Param(initialize=params["repair_cost"])

    model.weight = pyo.Var(
        model.repair_cases, domain=pyo.NonNegativeReals
    )
    model.production = pyo.Var(
        model.products,
        model.repair_cases,
        domain=pyo.NonNegativeReals,
    )

    model.case_weight_total = pyo.Constraint(
        expr=sum(model.weight[case] for case in model.repair_cases) == 1
    )

    def machine_capacity_rule(instance, case):
        return (
            sum(
                instance.hours[product] * instance.production[product, case]
                for product in instance.products
            )
            <= (
                instance.machine_hours_available
                + case * instance.extra_machine_hours
            )
            * instance.weight[case]
        )

    model.machine_capacity = pyo.Constraint(
        model.repair_cases, rule=machine_capacity_rule
    )

    def cash_availability_rule(instance, case):
        return (
            sum(
                (
                    instance.production_cost[product]
                    - instance.advance_rate[product]
                    * instance.selling_price[product]
                )
                * instance.production[product, case]
                for product in instance.products
            )
            <= (instance.available_cash - case * instance.repair_cost)
            * instance.weight[case]
        )

    model.cash_availability = pyo.Constraint(
        model.repair_cases, rule=cash_availability_rule
    )

    model.net_income = pyo.Objective(
        expr=sum(
            (
                model.selling_price[product]
                - model.production_cost[product]
            )
            * model.production[product, case]
            for product in model.products
            for case in model.repair_cases
        )
        - model.repair_cost * model.weight[1],
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.net_income))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}