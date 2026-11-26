# IR: {"sets":{"V":[1,2,3,4,5,6],"E":"{(i,j): i,j in V, i<j}","S":"{U subset V: 2<=|U|<=5}"},"params":{"cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_1_5":"real","cost_1_6":"real","cost_2_3":"real","cost_2_4":"real","cost_2_5":"real","cost_2_6":"real","cost_3_4":"real","cost_3_5":"real","cost_3_6":"real","cost_4_5":"real","cost_4_6":"real","cost_5_6":"real"},"decision_variables":{"x[i,j]":"binary for (i,j) in E"},"constraints":["For every v in V: sum(x[i,j] for (i,j) in E if i=v or j=v)=2","For every U in S: sum(x[i,j] for (i,j) in E if exactly one endpoint belongs to U)>=2"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(1, 7))
    edges = tuple(combinations(cities, 2))
    subsets = tuple(
        frozenset(subset)
        for size in range(2, len(cities))
        for subset in combinations(cities, size)
    )

    costs = {
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (1, 6): params["cost_1_6"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (2, 5): params["cost_2_5"],
        (2, 6): params["cost_2_6"],
        (3, 4): params["cost_3_4"],
        (3, 5): params["cost_3_5"],
        (3, 6): params["cost_3_6"],
        (4, 5): params["cost_4_5"],
        (4, 6): params["cost_4_6"],
        (5, 6): params["cost_5_6"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.cut_ids = pyo.Set(initialize=range(len(subsets)), ordered=True)
    model.travel_cost = pyo.Param(
        model.edges, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(instance, city):
        return sum(
            instance.x[i, j]
            for i, j in instance.edges
            if i == city or j == city
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.cities, rule=degree_rule
    )

    def connectivity_rule(instance, cut_id):
        subset = subsets[cut_id]
        return sum(
            instance.x[i, j]
            for i, j in instance.edges
            if (i in subset) != (j in subset)
        ) >= 2

    model.connectivity_constraints = pyo.Constraint(
        model.cut_ids, rule=connectivity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.edges
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}