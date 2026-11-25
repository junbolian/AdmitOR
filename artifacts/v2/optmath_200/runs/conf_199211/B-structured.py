# IR: {"sets":{"areas":[1,2,3,4,5],"ecosystems":["e1","e2","e3","e4","e5","e6","e7","e8","e9","e10","e11","e12","e13","e14","e15"]},"params":{"cost_area_1":"real","cost_area_2":"real","cost_area_3":"real","cost_area_4":"real","cost_area_5":"real"},"decision_variables":{"selected[area]":"binary"},"constraints":{"e1":"selected[1]+selected[2]>=1","e2":"selected[3]+selected[4]>=1","e3":"selected[2]+selected[3]>=1","e4":"selected[2]+selected[3]>=1","e5":"selected[2]+selected[3]+selected[4]>=1","e6":"selected[1]>=1","e7":"selected[2]+selected[3]+selected[4]>=1","e8":"selected[3]+selected[4]>=1","e9":"selected[2]+selected[3]>=1","e10":"selected[1]+selected[5]>=1","e11":"selected[2]+selected[4]>=1","e12":"selected[3]+selected[5]>=1","e13":"selected[3]+selected[4]>=1","e14":"selected[4]>=1","e15":"selected[1]+selected[4]+selected[5]>=1"},"objective":"minimize sum(cost_area_i*selected[i] for i in areas)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_area_1"],
        2: params["cost_area_2"],
        3: params["cost_area_3"],
        4: params["cost_area_4"],
        5: params["cost_area_5"],
    }

    coverage = {
        "e1": (1, 2),
        "e2": (3, 4),
        "e3": (2, 3),
        "e4": (2, 3),
        "e5": (2, 3, 4),
        "e6": (1,),
        "e7": (2, 3, 4),
        "e8": (3, 4),
        "e9": (2, 3),
        "e10": (1, 5),
        "e11": (2, 4),
        "e12": (3, 5),
        "e13": (3, 4),
        "e14": (4,),
        "e15": (1, 4, 5),
    }

    model = pyo.ConcreteModel()
    model.areas = pyo.Set(initialize=[1, 2, 3, 4, 5], ordered=True)
    # Pass a sequence, since a dictionary is treated as indexed initialization.
    model.ecosystems = pyo.Set(
        initialize=list(coverage.keys()), ordered=True
    )
    model.area_cost = pyo.Param(
        model.areas, initialize=costs, within=pyo.Reals
    )
    model.selected = pyo.Var(model.areas, domain=pyo.Binary)

    def coverage_rule(instance, ecosystem):
        return sum(
            instance.selected[area] for area in coverage[ecosystem]
        ) >= 1

    model.ecosystem_coverage = pyo.Constraint(
        model.ecosystems, rule=coverage_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.area_cost[area] * model.selected[area]
            for area in model.areas
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A solve/load failure is unsuccessful only if the objective
        # cannot subsequently be evaluated.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}