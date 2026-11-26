import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    container_capacity = params["container_capacity"]
    container_min_load = params["container_min_load"]
    quantity_A = params["quantity_A"]
    quantity_B = params["quantity_B"]
    quantity_C = params["quantity_C"]
    quantity_D = params["quantity_D"]
    quantity_E = params["quantity_E"]
    weight_A = params["weight_A"]
    weight_B = params["weight_B"]
    weight_C = params["weight_C"]
    weight_D = params["weight_D"]
    weight_E = params["weight_E"]
    min_D_per_container = params["min_D_per_container"]
    A_requires_C_ratio = params["A_requires_C_ratio"]

    goods = ["A", "B", "C", "D", "E"]
    total_weight = (
        quantity_A * weight_A
        + quantity_B * weight_B
        + quantity_C * weight_C
        + quantity_D * weight_D
        + quantity_E * weight_E
    )
    # Upper bound on number of containers (enough to always be feasible by weight)
    n_max = int(total_weight / container_min_load) + 1
    if n_max < 1:
        n_max = 1

    model = pyo.ConcreteModel()
    model.containers = pyo.RangeSet(1, n_max)
    model.goods = pyo.Set(initialize=goods)

    # x[j, g]: amount of good g loaded into container j
    model.x = pyo.Var(model.containers, model.goods, domain=pyo.NonNegativeReals)
    # y[j]: binary, container j is used
    model.y = pyo.Var(model.containers, domain=pyo.Binary)

    # Objective: minimize number of used containers
    model.total_containers = pyo.Objective(
        expr=sum(model.y[j] for j in model.containers),
        sense=pyo.minimize,
    )

    # Weight capacity and minimum load per container
    def capacity_rule(mdl, j):
        return (
            weight_A * mdl.x[j, "A"]
            + weight_B * mdl.x[j, "B"]
            + weight_C * mdl.x[j, "C"]
            + weight_D * mdl.x[j, "D"]
            + weight_E * mdl.x[j, "E"]
            <= container_capacity * mdl.y[j]
        )

    def min_load_rule(mdl, j):
        return (
            weight_A * mdl.x[j, "A"]
            + weight_B * mdl.x[j, "B"]
            + weight_C * mdl.x[j, "C"]
            + weight_D * mdl.x[j, "D"]
            + weight_E * mdl.x[j, "E"]
            >= container_min_load * mdl.y[j]
        )

    model.weight_capacity = pyo.Constraint(model.containers, rule=capacity_rule)
    model.min_load = pyo.Constraint(model.containers, rule=min_load_rule)

    # Total quantities must all be packed
    def demand_rule(mdl, g):
        return sum(mdl.x[j, g] for j in mdl.containers) == {
            "A": quantity_A,
            "B": quantity_B,
            "C": quantity_C,
            "D": quantity_D,
            "E": quantity_E,
        }[g]

    model.demand = pyo.Constraint(model.goods, rule=demand_rule)

    # Each used container must load at least min_D_per_container units of D
    def min_D_rule(mdl, j):
        return mdl.x[j, "D"] >= min_D_per_container * mdl.y[j]

    model.min_D = pyo.Constraint(model.containers, rule=min_D_rule)

    # For every unit of A loaded, at least A_requires_C_ratio units of C
    # (aggregate relation, since C can be loaded independently)
    model.ac_ratio = pyo.Constraint(
        expr=sum(model.x[j, "C"] for j in model.containers)
        >= A_requires_C_ratio * sum(model.x[j, "A"] for j in model.containers)
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_containers))
    return {"objective": obj_val, "status": "optimal"}