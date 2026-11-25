# IR: {"sets":{"C":"1..params[num_components] (frozen at 15)","E":"1..params[num_elements] (frozen at 14)","covers":{"1":[1,6,8,13],"2":[5,11,13,15],"3":[2,3,5,6,7,9],"4":[2,3,7,8,11],"5":[1,4,10,11,12],"6":[1,3,6,7,9,11,13],"7":[2,4,13],"8":[9,13,14],"9":[3,4,6,9,13],"10":[3,7,12,13],"11":[4,10,12,13,14],"12":[4,8,12],"13":[1,2,5,15],"14":[1,2,4,10,13]}},"params":{"component_cost":"cost indexed by C","coverage_requirement":"minimum coverage indexed by E","num_components":"frozen component count","num_elements":"frozen element count"},"variables":{"selected[c]":"binary for c in C"},"constraints":["For each e in E: sum(selected[c] for c in covers[e]) >= coverage_requirement[e]"],"objective":"minimize sum(component_cost[c]*selected[c] for c in C)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _indexed_values(data, size):
    """Accept a positional sequence or a mapping with 1-based integer/string keys."""
    if isinstance(data, Mapping):
        return {
            idx: data[idx] if idx in data else data[str(idx)]
            for idx in range(1, size + 1)
        }
    if len(data) != size:
        raise ValueError("Parameter sequence has an incorrect length.")
    return {idx: data[idx - 1] for idx in range(1, size + 1)}


def solve(params):
    num_components = params["num_components"]
    num_elements = params["num_elements"]
    component_cost = params["component_cost"]
    coverage_requirement = params["coverage_requirement"]

    if num_components != 15 or num_elements != 14:
        raise ValueError("The coverage structure is frozen at 15 components and 14 elements.")

    costs = _indexed_values(component_cost, int(num_components))
    requirements = _indexed_values(coverage_requirement, int(num_elements))

    covers = {
        1: (1, 6, 8, 13),
        2: (5, 11, 13, 15),
        3: (2, 3, 5, 6, 7, 9),
        4: (2, 3, 7, 8, 11),
        5: (1, 4, 10, 11, 12),
        6: (1, 3, 6, 7, 9, 11, 13),
        7: (2, 4, 13),
        8: (9, 13, 14),
        9: (3, 4, 6, 9, 13),
        10: (3, 7, 12, 13),
        11: (4, 10, 12, 13, 14),
        12: (4, 8, 12),
        13: (1, 2, 5, 15),
        14: (1, 2, 4, 10, 13),
    }

    model = pyo.ConcreteModel()
    model.components = pyo.RangeSet(1, int(num_components))
    model.elements = pyo.RangeSet(1, int(num_elements))
    model.component_cost = pyo.Param(model.components, initialize=costs)
    model.coverage_requirement = pyo.Param(model.elements, initialize=requirements)
    model.selected = pyo.Var(model.components, domain=pyo.Binary)

    def coverage_rule(network, element):
        return (
            sum(network.selected[component] for component in covers[element])
            >= network.coverage_requirement[element]
        )

    model.coverage_constraints = pyo.Constraint(
        model.elements, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.component_cost[component] * model.selected[component]
            for component in model.components
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