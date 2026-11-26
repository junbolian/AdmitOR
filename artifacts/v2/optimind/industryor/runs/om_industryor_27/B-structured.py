# IR: {"sets":{"cities":["Donghai","Nanjiang"],"specialties":[1,2,3],"types":[1,2,3,4,5,6],"eligible_specialties":{"1":[1,2],"2":[2,3],"3":[1,3],"4":[1,3],"5":[2,3],"6":[3]},"params":["demand_Donghai_1","demand_Donghai_2","demand_Donghai_3","demand_Nanjiang_1","demand_Nanjiang_2","demand_Nanjiang_3","count_type_1","count_type_2","count_type_3","count_type_4","count_type_5","count_type_6","p2_target","p3_target"],"structural_data":{"preferred_specialty":{"1":1,"2":2,"3":1,"4":3,"5":3,"6":3},"preferred_city":{"1":"Donghai","2":"Donghai","3":"Nanjiang","4":"Nanjiang","5":"Donghai","6":"Nanjiang"}},"variables":{"assignment[type,city,eligible_specialty]":"nonnegative integer","unmet[city,specialty]":"nonnegative real","specialty_shortfall":"nonnegative real","city_shortfall":"nonnegative real"},"constraints":["For each type: sum(assignment) <= count_type.","For each city and specialty: sum(assignment) + unmet = demand.","Preferred-specialty assignments + specialty_shortfall >= p2_target.","Preferred-city assignments + city_shortfall >= p3_target.","After each priority solve, constrain its expression <= its retrieved optimum."],"objective":{"sense":"lexicographic minimize","priorities":["sum(unmet)","specialty_shortfall","city_shortfall","sum(assignments to a nonpreferred city)"],"returned_value":"final minimum number assigned to a nonpreferred city"},"interpretation":{"targets":"minimum desired counts; exceeding them is not penalized","movement":"assignment to a city other than the preferred city, which is the only city-of-origin proxy supplied"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("Donghai", "Nanjiang")
    specialties = (1, 2, 3)
    personnel_types = (1, 2, 3, 4, 5, 6)

    eligible_specialties = {
        1: (1, 2),
        2: (2, 3),
        3: (1, 3),
        4: (1, 3),
        5: (2, 3),
        6: (3,),
    }
    preferred_specialty = {
        1: 1,
        2: 2,
        3: 1,
        4: 3,
        5: 3,
        6: 3,
    }
    preferred_city = {
        1: "Donghai",
        2: "Donghai",
        3: "Nanjiang",
        4: "Nanjiang",
        5: "Donghai",
        6: "Nanjiang",
    }

    demands = {
        ("Donghai", 1): params["demand_Donghai_1"],
        ("Donghai", 2): params["demand_Donghai_2"],
        ("Donghai", 3): params["demand_Donghai_3"],
        ("Nanjiang", 1): params["demand_Nanjiang_1"],
        ("Nanjiang", 2): params["demand_Nanjiang_2"],
        ("Nanjiang", 3): params["demand_Nanjiang_3"],
    }
    counts = {
        1: params["count_type_1"],
        2: params["count_type_2"],
        3: params["count_type_3"],
        4: params["count_type_4"],
        5: params["count_type_5"],
        6: params["count_type_6"],
    }

    assignment_keys = [
        (personnel_type, city, specialty)
        for personnel_type in personnel_types
        for city in cities
        for specialty in eligible_specialties[personnel_type]
    ]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.specialties = pyo.Set(initialize=specialties, ordered=True)
    model.personnel_types = pyo.Set(initialize=personnel_types, ordered=True)
    model.assignment_keys = pyo.Set(
        dimen=3, initialize=assignment_keys, ordered=True
    )

    model.demand_data = pyo.Param(
        model.cities,
        model.specialties,
        initialize=demands,
        within=pyo.NonNegativeReals,
    )
    model.count_data = pyo.Param(
        model.personnel_types,
        initialize=counts,
        within=pyo.NonNegativeReals,
    )
    model.specialty_target = pyo.Param(
        initialize=params["p2_target"], within=pyo.NonNegativeReals
    )
    model.city_target = pyo.Param(
        initialize=params["p3_target"], within=pyo.NonNegativeReals
    )

    model.assignment = pyo.Var(
        model.assignment_keys, domain=pyo.NonNegativeIntegers
    )
    model.unmet = pyo.Var(
        model.cities, model.specialties, domain=pyo.NonNegativeReals
    )
    model.specialty_shortfall = pyo.Var(domain=pyo.NonNegativeReals)
    model.city_shortfall = pyo.Var(domain=pyo.NonNegativeReals)

    def availability_rule(mod, personnel_type):
        return sum(
            mod.assignment[personnel_type, city, specialty]
            for city in cities
            for specialty in eligible_specialties[personnel_type]
        ) <= mod.count_data[personnel_type]

    model.availability_constraints = pyo.Constraint(
        model.personnel_types, rule=availability_rule
    )

    def demand_rule(mod, city, specialty):
        return (
            sum(
                mod.assignment[personnel_type, city, specialty]
                for personnel_type in personnel_types
                if specialty in eligible_specialties[personnel_type]
            )
            + mod.unmet[city, specialty]
            == mod.demand_data[city, specialty]
        )

    model.demand_constraints = pyo.Constraint(
        model.cities, model.specialties, rule=demand_rule
    )

    model.preferred_specialty_count = pyo.Expression(
        expr=sum(
            model.assignment[personnel_type, city, specialty]
            for personnel_type, city, specialty in assignment_keys
            if specialty == preferred_specialty[personnel_type]
        )
    )
    model.preferred_city_count = pyo.Expression(
        expr=sum(
            model.assignment[personnel_type, city, specialty]
            for personnel_type, city, specialty in assignment_keys
            if city == preferred_city[personnel_type]
        )
    )

    model.specialty_goal_constraint = pyo.Constraint(
        expr=model.preferred_specialty_count + model.specialty_shortfall
        >= model.specialty_target
    )
    model.city_goal_constraint = pyo.Constraint(
        expr=model.preferred_city_count + model.city_shortfall
        >= model.city_target
    )

    model.total_unmet = pyo.Expression(
        expr=sum(
            model.unmet[city, specialty]
            for city in cities
            for specialty in specialties
        )
    )
    model.total_moves = pyo.Expression(
        expr=sum(
            model.assignment[personnel_type, city, specialty]
            for personnel_type, city, specialty in assignment_keys
            if city != preferred_city[personnel_type]
        )
    )

    model.priority_bounds = pyo.ConstraintList()
    model.goal_objective = pyo.Objective(
        expr=model.total_unmet, sense=pyo.minimize
    )

    # Optimize each priority and preserve its optimum before the next solve.
    for priority_expression in (
        model.total_unmet,
        model.specialty_shortfall,
        model.city_shortfall,
    ):
        model.goal_objective.set_value(priority_expression)

        try:
            Highs().solve(model)
        except RuntimeError:
            return {"objective": None, "status": "solve_failed"}

        try:
            obj_val = float(pyo.value(model.goal_objective))
        except (ValueError, TypeError):
            return {"objective": None, "status": "objective_unavailable"}

        model.priority_bounds.add(priority_expression <= obj_val)

    model.goal_objective.set_value(model.total_moves)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.goal_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}