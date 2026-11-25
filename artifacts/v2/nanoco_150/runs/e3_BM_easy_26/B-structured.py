# IR: {"sets":{"stations":[0,1,2,3,4,5,6,7,8,9],"links":[[0,3],[0,4],[1,8],[2,3],[2,6],[2,7],[3,6],[3,7],[3,8],[3,9],[4,5],[4,6],[4,7],[4,8],[4,9],[5,7],[6,7]]},"params":{"revenue[i,j]":"params['revenue_'+str(i)+'_'+str(j)] for each candidate link (i,j)","capacity[s]":"params['capacity_'+str(s)] for each station s"},"variables":{"selected[i,j]":{"type":"binary","index":"links"}},"constraints":["For each station s: sum(selected[i,j] for candidate links incident to s) <= capacity[s]."],"objective":{"sense":"maximize","expression":"sum(revenue[i,j] * selected[i,j] for (i,j) in links)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    stations = tuple(range(10))
    links = (
        (0, 3),
        (0, 4),
        (1, 8),
        (2, 3),
        (2, 6),
        (2, 7),
        (3, 6),
        (3, 7),
        (3, 8),
        (3, 9),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (4, 9),
        (5, 7),
        (6, 7),
    )

    revenues = {
        (i, j): params[f"revenue_{i}_{j}"]
        for i, j in links
    }
    capacities = {
        station: params[f"capacity_{station}"]
        for station in stations
    }
    incident_links = {
        station: tuple(
            (i, j) for i, j in links
            if station == i or station == j
        )
        for station in stations
    }

    model = pyo.ConcreteModel()
    model.stations = pyo.Set(initialize=stations, ordered=True)
    model.links = pyo.Set(initialize=links, dimen=2, ordered=True)

    model.revenue = pyo.Param(
        model.links,
        initialize=revenues,
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.stations,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.selected = pyo.Var(model.links, domain=pyo.Binary)

    def port_capacity_rule(network, station):
        return (
            sum(
                network.selected[i, j]
                for i, j in incident_links[station]
            )
            <= network.capacity[station]
        )

    model.port_capacity = pyo.Constraint(
        model.stations,
        rule=port_capacity_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[i, j] * model.selected[i, j]
            for i, j in model.links
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}