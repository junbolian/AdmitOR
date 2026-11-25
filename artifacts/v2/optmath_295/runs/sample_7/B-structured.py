# IR: {"sets":{"cities":"0..6","links":"[(i,j) for i in cities for j in cities if i != j], ordered lexicographically"},"params":{"transport_cost":"real[links], from params['transport_cost'] in link order","node_net_demand":"real[cities], from params['node_net_demand']","node_capacity":"real[cities], from params['node_capacity']","link_capacity":"real[links], from params['link_capacity'] in link order"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in links"},"constraints":["For each city i: sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) = node_net_demand[i]","For each city i: sum(flow[j,i] for j != i) <= node_capacity[i]","For each link (i,j): flow[i,j] <= link_capacity[i,j]"],"objective":"minimize sum(transport_cost[i,j] * flow[i,j] for (i,j) in links)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    links = [(i, j) for i in cities for j in cities if i != j]

    transport_cost = params["transport_cost"]
    node_net_demand = params["node_net_demand"]
    node_capacity = params["node_capacity"]
    link_capacity = params["link_capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.links = pyo.Set(dimen=2, initialize=links, ordered=True)

    model.transport_cost = pyo.Param(
        model.links,
        initialize={
            link: transport_cost[position]
            for position, link in enumerate(links)
        },
        within=pyo.Reals,
    )
    model.node_net_demand = pyo.Param(
        model.cities,
        initialize={i: node_net_demand[i] for i in cities},
        within=pyo.Reals,
    )
    model.node_capacity = pyo.Param(
        model.cities,
        initialize={i: node_capacity[i] for i in cities},
        within=pyo.Reals,
    )
    model.link_capacity = pyo.Param(
        model.links,
        initialize={
            link: link_capacity[position]
            for position, link in enumerate(links)
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.links, domain=pyo.NonNegativeReals)

    def balance_rule(instance, i):
        inflow = sum(
            instance.flow[j, i] for j in instance.cities if j != i
        )
        outflow = sum(
            instance.flow[i, j] for j in instance.cities if j != i
        )
        return inflow - outflow == instance.node_net_demand[i]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )

    def receiving_capacity_rule(instance, i):
        return (
            sum(instance.flow[j, i] for j in instance.cities if j != i)
            <= instance.node_capacity[i]
        )

    model.receiving_capacity_limit = pyo.Constraint(
        model.cities, rule=receiving_capacity_rule
    )

    def link_capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.link_capacity[i, j]

    model.link_capacity_limit = pyo.Constraint(
        model.links, rule=link_capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
            for i, j in model.links
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