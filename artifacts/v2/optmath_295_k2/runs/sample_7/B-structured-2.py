# IR: {"sets":{"cities":"0..6","links":"[(i,j) for i in cities for j in cities if i != j], in lexicographic order"},"params":{"costs":"real[links], from params['costs'] in link order","net_demands":"real[cities], from params['net_demands']","city_capacity":"nonnegative real[cities], from params['city_capacity']","link_capacity":"nonnegative real[links], from params['link_capacity'] in link order"},"variables":{"flow[i,j]":"continuous nonnegative real for each link"},"constraints":["For each city i: sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == net_demands[i]","For each city i: sum(flow[j,i] for j != i) <= city_capacity[i]","For each link (i,j): flow[i,j] <= link_capacity[i,j]"],"objective":"Minimize sum(costs[i,j] * flow[i,j] for (i,j) in links)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    links = [(i, j) for i in cities for j in cities if i != j]

    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.links = pyo.Set(dimen=2, initialize=links, ordered=True)

    model.costs = pyo.Param(
        model.links,
        initialize={arc: costs[k] for k, arc in enumerate(links)},
        within=pyo.Reals,
    )
    model.net_demands = pyo.Param(
        model.cities,
        initialize={i: net_demands[i] for i in cities},
        within=pyo.Reals,
    )
    model.city_capacity = pyo.Param(
        model.cities,
        initialize={i: city_capacity[i] for i in cities},
        within=pyo.NonNegativeReals,
    )
    model.link_capacity = pyo.Param(
        model.links,
        initialize={arc: link_capacity[k] for k, arc in enumerate(links)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    def flow_balance_rule(model, i):
        incoming = sum(model.flow[j, i] for j in model.cities if j != i)
        outgoing = sum(model.flow[i, j] for j in model.cities if j != i)
        return incoming - outgoing == model.net_demands[i]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=flow_balance_rule
    )

    def receiving_capacity_rule(model, i):
        return (
            sum(model.flow[j, i] for j in model.cities if j != i)
            <= model.city_capacity[i]
        )

    model.receiving_capacity = pyo.Constraint(
        model.cities, rule=receiving_capacity_rule
    )

    def shipping_capacity_rule(model, i, j):
        return model.flow[i, j] <= model.link_capacity[i, j]

    model.shipping_capacity = pyo.Constraint(
        model.links, rule=shipping_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[i, j] * model.flow[i, j]
            for i, j in model.links
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}