# IR: {"sets":{"V":"range(num_substances)","K":"range(num_substances)","E":"range(num_incompatibility_edges)"},"params":{"num_substances":"number of substances","num_incompatibility_edges":"number of edges","edge_list":"edge endpoints indexed by E"},"variables":{"x[v,k]":"binary; substance v uses section k","y[k]":"binary; section k is used"},"constraints":["sum(x[v,k] for k in K) == 1 for v in V","x[v,k] <= y[k] for v in V, k in K","x[edge_list[e][0],k] + x[edge_list[e][1],k] <= 1 for e in E, k in K"],"objective":"minimize sum(y[k] for k in K)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_substances = params["num_substances"]
    num_incompatibility_edges = params["num_incompatibility_edges"]
    edge_list = params["edge_list"]

    if num_substances < 0 or num_incompatibility_edges < 0:
        raise ValueError("Set sizes must be nonnegative.")
    if len(edge_list) != num_incompatibility_edges:
        raise ValueError("edge_list length must match num_incompatibility_edges.")

    for endpoints in edge_list:
        if len(endpoints) != 2:
            raise ValueError("Each edge must contain two substance indices.")
        for vertex in endpoints:
            if vertex not in range(num_substances):
                raise ValueError("Edge endpoint is outside the substance index set.")

    model = pyo.ConcreteModel()

    model.substances = pyo.Set(
        initialize=range(num_substances), ordered=True
    )
    model.sections = pyo.Set(
        initialize=range(num_substances), ordered=True
    )
    model.edge_ids = pyo.Set(
        initialize=range(num_incompatibility_edges), ordered=True
    )

    model.x = pyo.Var(
        model.substances, model.sections, domain=pyo.Binary
    )
    model.y = pyo.Var(model.sections, domain=pyo.Binary)

    def assignment_rule(model, vertex):
        return sum(
            model.x[vertex, section] for section in model.sections
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.substances, rule=assignment_rule
    )

    def section_usage_rule(model, vertex, section):
        return model.x[vertex, section] <= model.y[section]

    model.section_usage_constraints = pyo.Constraint(
        model.substances, model.sections, rule=section_usage_rule
    )

    def incompatibility_rule(model, edge_id, section):
        first_vertex, second_vertex = edge_list[edge_id]
        return (
            model.x[first_vertex, section]
            + model.x[second_vertex, section]
            <= 1
        )

    model.incompatibility_constraints = pyo.Constraint(
        model.edge_ids, model.sections, rule=incompatibility_rule
    )

    model.total_sections = pyo.Objective(
        expr=sum(model.y[section] for section in model.sections),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_sections))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}