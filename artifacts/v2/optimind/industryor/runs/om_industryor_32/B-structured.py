# IR: {"sets":{"G":["A","B","C","D","E"],"J":"1..N","N":"max(1,min(sum_g quantity[g],quantity[D]//ceil(min_D_per_container))) if min_D_per_container>0 else max(1,sum_g quantity[g])"},"params":{"container_capacity":"nonnegative real","container_min_load":"nonnegative real","quantity_A":"nonnegative integer","quantity_B":"nonnegative integer","quantity_C":"nonnegative integer","quantity_D":"nonnegative integer","quantity_E":"nonnegative integer","weight_A":"nonnegative real","weight_B":"nonnegative real","weight_C":"nonnegative real","weight_D":"nonnegative real","weight_E":"nonnegative real","min_D_per_container":"nonnegative real","A_requires_C_ratio":"nonnegative real"},"variables":{"x[g,j]":"nonnegative integer units of good g in container j","used[j]":"binary"},"constraints":["sum_j x[g,j] = quantity[g] for each g","x[g,j] <= quantity[g]*used[j] for each g,j","sum_g weight[g]*x[g,j] <= container_capacity*used[j] for each j","sum_g weight[g]*x[g,j] >= container_min_load*used[j] for each j","x[D,j] >= min_D_per_container*used[j] for each j","x[C,j] >= A_requires_C_ratio*x[A,j] for each j","used[j] >= used[j+1] for each j<N"],"objective":"minimize sum_j used[j]"}

from math import ceil

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    quantities = {
        "A": params["quantity_A"],
        "B": params["quantity_B"],
        "C": params["quantity_C"],
        "D": params["quantity_D"],
        "E": params["quantity_E"],
    }
    weights = {
        "A": params["weight_A"],
        "B": params["weight_B"],
        "C": params["weight_C"],
        "D": params["weight_D"],
        "E": params["weight_E"],
    }

    model = pyo.ConcreteModel()
    model.goods = pyo.Set(initialize=("A", "B", "C", "D", "E"), ordered=True)

    model.quantity = pyo.Param(
        model.goods, initialize=quantities, within=pyo.NonNegativeIntegers
    )
    model.weight = pyo.Param(
        model.goods, initialize=weights, within=pyo.NonNegativeReals
    )
    model.container_capacity = pyo.Param(
        initialize=params["container_capacity"], within=pyo.NonNegativeReals
    )
    model.container_min_load = pyo.Param(
        initialize=params["container_min_load"], within=pyo.NonNegativeReals
    )
    model.min_D_per_container = pyo.Param(
        initialize=params["min_D_per_container"], within=pyo.NonNegativeReals
    )
    model.A_requires_C_ratio = pyo.Param(
        initialize=params["A_requires_C_ratio"], within=pyo.NonNegativeReals
    )

    # Each nonempty container holds at least one unit. A positive D
    # requirement further bounds the number of usable containers.
    total_units = sum(
        int(pyo.value(model.quantity[good])) for good in model.goods
    )
    minimum_d = pyo.value(model.min_D_per_container)
    if minimum_d > 0:
        d_bound = int(pyo.value(model.quantity["D"])) // ceil(minimum_d)
        container_count = max(1, min(total_units, d_bound))
    else:
        container_count = max(1, total_units)

    model.containers = pyo.RangeSet(1, container_count)
    model.x = pyo.Var(
        model.goods, model.containers, domain=pyo.NonNegativeIntegers
    )
    model.used = pyo.Var(model.containers, domain=pyo.Binary)

    def inventory_rule(instance, good):
        return (
            sum(instance.x[good, container] for container in instance.containers)
            == instance.quantity[good]
        )

    model.inventory_balance = pyo.Constraint(
        model.goods, rule=inventory_rule
    )

    def activation_rule(instance, good, container):
        return (
            instance.x[good, container]
            <= instance.quantity[good] * instance.used[container]
        )

    model.container_activation = pyo.Constraint(
        model.goods, model.containers, rule=activation_rule
    )

    def load_rule(instance, container):
        return sum(
            instance.weight[good] * instance.x[good, container]
            for good in instance.goods
        )

    model.container_load = pyo.Expression(
        model.containers, rule=load_rule
    )

    def capacity_rule(instance, container):
        return (
            instance.container_load[container]
            <= instance.container_capacity * instance.used[container]
        )

    model.capacity_limit = pyo.Constraint(
        model.containers, rule=capacity_rule
    )

    def minimum_load_rule(instance, container):
        return (
            instance.container_load[container]
            >= instance.container_min_load * instance.used[container]
        )

    model.minimum_load_requirement = pyo.Constraint(
        model.containers, rule=minimum_load_rule
    )

    def minimum_d_rule(instance, container):
        return (
            instance.x["D", container]
            >= instance.min_D_per_container * instance.used[container]
        )

    model.minimum_d_requirement = pyo.Constraint(
        model.containers, rule=minimum_d_rule
    )

    def pairing_rule(instance, container):
        return (
            instance.x["C", container]
            >= instance.A_requires_C_ratio * instance.x["A", container]
        )

    model.a_c_pairing = pyo.Constraint(
        model.containers, rule=pairing_rule
    )

    def symmetry_rule(instance, container):
        if container == container_count:
            return pyo.Constraint.Skip
        return instance.used[container] >= instance.used[container + 1]

    model.container_order = pyo.Constraint(
        model.containers, rule=symmetry_rule
    )

    model.total_containers = pyo.Objective(
        expr=sum(model.used[container] for container in model.containers),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_containers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}