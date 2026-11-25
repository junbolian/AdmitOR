# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3]},"params":{"cost":"cost[p][c]","capacity":"capacity[p]","contract_demand":"contract_demand[c]","min_delivery":"min_delivery[p]","min_producers_per_contract":"scalar"},"variables":{"delivery[p,c]":"continuous >= 0","assigned[p,c]":"binary"},"constraints":["sum_c delivery[p,c] <= capacity[p] for each p","sum_p delivery[p,c] >= contract_demand[c] for each c","delivery[p,c] >= min_delivery[p]*assigned[p,c] for each p,c","delivery[p,c] <= capacity[p]*assigned[p,c] for each p,c","sum_p assigned[p,c] >= min_producers_per_contract for each c"],"objective":"minimize sum_p,c cost[p,c]*delivery[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    contract_demand = params["contract_demand"]
    min_delivery = params["min_delivery"]
    min_producers_per_contract = params["min_producers_per_contract"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 3)

    model.cost = pyo.Param(
        model.P, model.C,
        initialize={(p, c): cost[p][c] for p in model.P for c in model.C},
    )
    model.capacity = pyo.Param(
        model.P, initialize={p: capacity[p] for p in model.P}
    )
    model.contract_demand = pyo.Param(
        model.C, initialize={c: contract_demand[c] for c in model.C}
    )
    model.min_delivery = pyo.Param(
        model.P, initialize={p: min_delivery[p] for p in model.P}
    )
    model.min_producers_per_contract = pyo.Param(
        initialize=min_producers_per_contract
    )

    model.delivery = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.assigned = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(instance, p):
        return sum(instance.delivery[p, c] for c in instance.C) <= instance.capacity[p]

    model.capacity_limits = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(instance, c):
        return (
            sum(instance.delivery[p, c] for p in instance.P)
            >= instance.contract_demand[c]
        )

    model.demand_requirements = pyo.Constraint(model.C, rule=demand_rule)

    def minimum_delivery_rule(instance, p, c):
        return (
            instance.delivery[p, c]
            >= instance.min_delivery[p] * instance.assigned[p, c]
        )

    model.minimum_delivery_links = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def assignment_upper_rule(instance, p, c):
        return (
            instance.delivery[p, c]
            <= instance.capacity[p] * instance.assigned[p, c]
        )

    model.assignment_upper_links = pyo.Constraint(
        model.P, model.C, rule=assignment_upper_rule
    )

    def producer_count_rule(instance, c):
        return (
            sum(instance.assigned[p, c] for p in instance.P)
            >= instance.min_producers_per_contract
        )

    model.producer_count_requirements = pyo.Constraint(
        model.C, rule=producer_count_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[p, c] * model.delivery[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}