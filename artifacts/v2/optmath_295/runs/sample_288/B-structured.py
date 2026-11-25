# IR: {"sets":{"R":"range(num_resources)","J":"range(num_centers_available)"},"params":{"resource_weights":"resource weight indexed by R","center_capacity":"uniform center capacity","num_resources":"resource index-set size","num_centers_available":"available-center index-set size"},"variables":{"x[r,j]":"binary; resource r assigned to center j","y[j]":"binary; center j used"},"constraints":["For each r: sum_j x[r,j] = 1","For each j: sum_r resource_weights[r]*x[r,j] <= center_capacity*y[j]","For each r,j: x[r,j] <= y[j]","For each j: y[j] <= sum_r x[r,j]"],"objective":"minimize sum_j y[j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]
    num_resources = params["num_resources"]
    num_centers_available = params["num_centers_available"]

    model = pyo.ConcreteModel()

    model.resources = pyo.Set(
        initialize=range(num_resources), ordered=True
    )
    model.centers = pyo.Set(
        initialize=range(num_centers_available), ordered=True
    )

    model.resource_weight = pyo.Param(
        model.resources,
        initialize={
            resource_idx: resource_weights[resource_idx]
            for resource_idx in range(num_resources)
        },
    )
    model.capacity = pyo.Param(initialize=center_capacity)

    model.assignment = pyo.Var(
        model.resources, model.centers, domain=pyo.Binary
    )
    model.center_used = pyo.Var(model.centers, domain=pyo.Binary)

    def assignment_rule(instance, resource_idx):
        return (
            pyo.quicksum(
                instance.assignment[resource_idx, center_idx]
                for center_idx in instance.centers
            )
            == 1
        )

    model.exactly_one_center = pyo.Constraint(
        model.resources, rule=assignment_rule
    )

    def capacity_rule(instance, center_idx):
        return (
            pyo.quicksum(
                instance.resource_weight[resource_idx]
                * instance.assignment[resource_idx, center_idx]
                for resource_idx in instance.resources
            )
            <= instance.capacity * instance.center_used[center_idx]
        )

    model.center_capacity_limit = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    def assignment_requires_use_rule(instance, resource_idx, center_idx):
        return (
            instance.assignment[resource_idx, center_idx]
            <= instance.center_used[center_idx]
        )

    model.assignment_requires_use = pyo.Constraint(
        model.resources,
        model.centers,
        rule=assignment_requires_use_rule,
    )

    def used_center_nonempty_rule(instance, center_idx):
        return (
            instance.center_used[center_idx]
            <= pyo.quicksum(
                instance.assignment[resource_idx, center_idx]
                for resource_idx in instance.resources
            )
        )

    model.used_center_nonempty = pyo.Constraint(
        model.centers, rule=used_center_nonempty_rule
    )

    model.total_centers = pyo.Objective(
        expr=pyo.quicksum(
            model.center_used[center_idx]
            for center_idx in model.centers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_centers))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}