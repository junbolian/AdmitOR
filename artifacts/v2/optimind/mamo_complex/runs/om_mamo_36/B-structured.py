# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"demand":"six-element sequence ordered Jan-Jun","regular_capacity":"scalar","regular_cost":"scalar","overtime_capacity":"scalar","overtime_cost":"scalar","inventory_cost":"scalar","initial_inventory":"scalar"},"variables":{"regular[t]":"nonnegative continuous","overtime[t]":"nonnegative continuous","inventory[t]":"nonnegative continuous, end-of-month"},"constraints":["regular[t] <= regular_capacity for t in T","overtime[t] <= overtime_capacity for t in T","initial_inventory + regular[0] + overtime[0] - inventory[0] = demand[0]","inventory[t-1] + regular[t] + overtime[t] - inventory[t] = demand[t] for t in T with t > 0"],"objective":"minimize sum(regular_cost*regular[t] + overtime_cost*overtime[t] + inventory_cost*inventory[t] for t in T)","report":"objective rounded to nearest integer and returned as float"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the six-month production plan; demand must be ordered Jan-Jun."""
    demand = params["demand"]
    regular_capacity = params["regular_capacity"]
    regular_cost = params["regular_cost"]
    overtime_capacity = params["overtime_capacity"]
    overtime_cost = params["overtime_cost"]
    inventory_cost = params["inventory_cost"]
    initial_inventory = params["initial_inventory"]

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(0, 5)

    model.monthly_demand = pyo.Param(
        model.months,
        initialize={t: demand[t] for t in range(6)},
        within=pyo.NonNegativeReals,
    )
    model.regular_capacity = pyo.Param(
        initialize=regular_capacity, within=pyo.NonNegativeReals
    )
    model.regular_cost = pyo.Param(
        initialize=regular_cost, within=pyo.NonNegativeReals
    )
    model.overtime_capacity = pyo.Param(
        initialize=overtime_capacity, within=pyo.NonNegativeReals
    )
    model.overtime_cost = pyo.Param(
        initialize=overtime_cost, within=pyo.NonNegativeReals
    )
    model.inventory_cost = pyo.Param(
        initialize=inventory_cost, within=pyo.NonNegativeReals
    )
    model.initial_inventory = pyo.Param(
        initialize=initial_inventory, within=pyo.NonNegativeReals
    )

    model.regular = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.overtime = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def regular_limit_rule(instance, t):
        return instance.regular[t] <= instance.regular_capacity

    model.regular_limit = pyo.Constraint(
        model.months, rule=regular_limit_rule
    )

    def overtime_limit_rule(instance, t):
        return instance.overtime[t] <= instance.overtime_capacity

    model.overtime_limit = pyo.Constraint(
        model.months, rule=overtime_limit_rule
    )

    def inventory_balance_rule(instance, t):
        beginning_inventory = (
            instance.initial_inventory
            if t == 0
            else instance.inventory[t - 1]
        )
        return (
            beginning_inventory
            + instance.regular[t]
            + instance.overtime[t]
            - instance.inventory[t]
            == instance.monthly_demand[t]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.regular_cost * model.regular[t]
            + model.overtime_cost * model.overtime[t]
            + model.inventory_cost * model.inventory[t]
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when it cannot load a feasible solution.
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}