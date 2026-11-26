# IR: {"sets":{"products":[0,1,2],"quarters":[0,1,2,3]},"params":{"demand":"nonnegative 3x4 matrix","initial_inventory":"nonnegative length-3 vector","final_inventory":"nonnegative length-3 vector","production_hours_per_quarter":"nonnegative scalar","unit_hours":"nonnegative length-3 vector","compensation_cost":"nonnegative length-3 vector","storage_cost":"nonnegative scalar"},"variables":{"production[p,q]":"NonNegativeReals","inventory[p,q]":"NonNegativeReals, end-of-quarter stock","backlog[p,q]":"NonNegativeReals, end-of-quarter overdue demand"},"constraints":["inventory[p,0]-backlog[p,0]=initial_inventory[p]+production[p,0]-demand[p,0]","inventory[p,q]-backlog[p,q]=inventory[p,q-1]-backlog[p,q-1]+production[p,q]-demand[p,q] for q>0","sum_p unit_hours[p]*production[p,q]<=production_hours_per_quarter for each q","production[0,1]=0","inventory[p,3]=final_inventory[p] for each p","backlog[p,3]=0 for each p"],"objective":"minimize sum_{p,q}(compensation_cost[p]*backlog[p,q]+storage_cost*inventory[p,q])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]
    production_hours_per_quarter = params["production_hours_per_quarter"]
    unit_hours = params["unit_hours"]
    compensation_cost = params["compensation_cost"]
    storage_cost = params["storage_cost"]

    model = pyo.ConcreteModel()

    model.products = pyo.RangeSet(0, 2)
    model.quarters = pyo.RangeSet(0, 3)

    model.bookings = pyo.Param(
        model.products,
        model.quarters,
        initialize=lambda mdl, product, quarter: demand[product][quarter],
        within=pyo.NonNegativeReals,
    )
    model.starting_stock = pyo.Param(
        model.products,
        initialize=lambda mdl, product: initial_inventory[product],
        within=pyo.NonNegativeReals,
    )
    model.required_final_stock = pyo.Param(
        model.products,
        initialize=lambda mdl, product: final_inventory[product],
        within=pyo.NonNegativeReals,
    )
    model.hour_capacity = pyo.Param(
        initialize=production_hours_per_quarter,
        within=pyo.NonNegativeReals,
    )
    model.hours_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: unit_hours[product],
        within=pyo.NonNegativeReals,
    )
    model.late_cost_per_unit = pyo.Param(
        model.products,
        initialize=lambda mdl, product: compensation_cost[product],
        within=pyo.NonNegativeReals,
    )
    model.holding_cost_per_unit = pyo.Param(
        initialize=storage_cost,
        within=pyo.NonNegativeReals,
    )

    model.production = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )
    model.backlog = pyo.Var(
        model.products, model.quarters, domain=pyo.NonNegativeReals
    )

    def balance_rule(mdl, product, quarter):
        if quarter == 0:
            previous_net_stock = mdl.starting_stock[product]
        else:
            previous_net_stock = (
                mdl.inventory[product, quarter - 1]
                - mdl.backlog[product, quarter - 1]
            )

        return (
            mdl.inventory[product, quarter] - mdl.backlog[product, quarter]
            == previous_net_stock
            + mdl.production[product, quarter]
            - mdl.bookings[product, quarter]
        )

    model.stock_balance = pyo.Constraint(
        model.products, model.quarters, rule=balance_rule
    )

    def capacity_rule(mdl, quarter):
        return (
            sum(
                mdl.hours_per_unit[product] * mdl.production[product, quarter]
                for product in mdl.products
            )
            <= mdl.hour_capacity
        )

    model.production_capacity = pyo.Constraint(
        model.quarters, rule=capacity_rule
    )

    model.equipment_outage = pyo.Constraint(
        expr=model.production[0, 1] == 0
    )

    model.ending_inventory_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: (
            mdl.inventory[product, 3] == mdl.required_final_stock[product]
        ),
    )

    model.year_end_delivery_requirement = pyo.Constraint(
        model.products,
        rule=lambda mdl, product: mdl.backlog[product, 3] == 0,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.late_cost_per_unit[product] * model.backlog[product, quarter]
            + model.holding_cost_per_unit * model.inventory[product, quarter]
            for product in model.products
            for quarter in model.quarters
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}