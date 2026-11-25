# IR: {"sets":{"cities":"0..6","links":"(i,j) in cities x cities with i != j, ordered lexicographically"},"params":{"costs":"real[links], from params['costs'] in link order","net_demands":"real[cities], from params['net_demands']","city_capacity":"nonnegative real[cities], from params['city_capacity']","link_capacity":"nonnegative real[links], from params['link_capacity'] in link order"},"variables":{"flow[i,j]":"nonnegative continuous for each link"},"constraints":{"balance[i]":"sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == net_demands[i]","receiving_limit[i]":"sum(flow[j,i] for j != i) <= city_capacity[i]","shipping_limit[i,j]":"flow[i,j] <= link_capacity[i,j]"},"objective":"minimize sum(costs[i,j] * flow[i,j] for (i,j) in links)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    links = [
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    ]

    costs = params["costs"]
    net_demands = params["net_demands"]
    city_capacity = params["city_capacity"]
    link_capacity = params["link_capacity"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.links = pyo.Set(initialize=links, dimen=2, ordered=True)

    model.costs = pyo.Param(
        model.links,
        initialize={link: costs[position] for position, link in enumerate(links)},
        within=pyo.Reals,
    )
    model.net_demands = pyo.Param(
        model.cities,
        initialize={city: net_demands[city] for city in cities},
        within=pyo.Reals,
    )
    model.city_capacity = pyo.Param(
        model.cities,
        initialize={city: city_capacity[city] for city in cities},
        within=pyo.NonNegativeReals,
    )
    model.link_capacity = pyo.Param(
        model.links,
        initialize={
            link: link_capacity[position]
            for position, link in enumerate(links)
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, city):
        incoming = sum(
            mdl.flow[other, city] for other in mdl.cities if other != city
        )
        outgoing = sum(
            mdl.flow[city, other] for other in mdl.cities if other != city
        )
        return incoming - outgoing == mdl.net_demands[city]

    def receiving_limit_rule(mdl, city):
        return (
            sum(mdl.flow[other, city] for other in mdl.cities if other != city)
            <= mdl.city_capacity[city]
        )

    def shipping_limit_rule(mdl, origin, destination):
        return (
            mdl.flow[origin, destination]
            <= mdl.link_capacity[origin, destination]
        )

    model.balance = pyo.Constraint(model.cities, rule=balance_rule)
    model.receiving_limit = pyo.Constraint(
        model.cities, rule=receiving_limit_rule
    )
    model.shipping_limit = pyo.Constraint(
        model.links, rule=shipping_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.costs[origin, destination] * model.flow[origin, destination]
            for origin, destination in model.links
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