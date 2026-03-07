%% =====================================================
%%  TRAFFIC VIOLATIONS EXPLAINABLE SYSTEM (Pure Prolog)
%%  File: traffic_violations.pl
%%  SWI-Prolog 8.4+ recommended
%%  Author: Your College Project (2026)
%%  Updated: Added 5 new violations
%%           1. Seatbelt Violation
%%           2. Phone Usage Violation
%%           3. Overloading Violation
%%           4. No Parking Violation
%%           5. Speed Breaker Violation
%% =====================================================

:- module(traffic_violations, [
    assert_facts/1,
    retract_all_facts/0,
    violation/2,
    explain_violation/3,
    list_all_violations/1,
    clear_knowledge_base/0
]).

:- use_module(library(persistency)).
:- use_module(library(tabling)).
:- use_module(library(lists)).

% =====================================================
% 1. DYNAMIC FACTS (asserted by your Python CV module)
% =====================================================
:- dynamic
    vehicle/2,                  % vehicle(Id, Type)          e.g. vehicle(car_001, car)
    traffic_light/2,            % traffic_light(State, Time) e.g. traffic_light(red, t42)
    crossed_stop_line/2,        % crossed_stop_line(Id, Time)
    speed/2,                    % speed(Id, Kmph)
    in_wrong_lane/2,            % in_wrong_lane(Id, LaneType)
    helmet/2,                   % helmet(Id, Wearing)         Wearing = yes/no
    emergency_vehicle/1,        % emergency_vehicle(Id)
    direction/2,                % direction(Id, Dir)          Dir = wrong_way/u_turn
    frame_time/1,               % current frame timestamp

    % --- NEW DYNAMIC FACTS ---
    seatbelt/2,                 % seatbelt(Id, yes/no)
    phone_usage/2,              % phone_usage(Id, yes/no)
    passenger_count/2,          % passenger_count(Id, N)
    parked/2,                   % parked(Id, yes/no)
    zone_type/2,                % zone_type(Id, no_parking/normal)
    near_speed_breaker/2.       % near_speed_breaker(Id, yes/no)

% =====================================================
% 2. TABLED PREDICATES (for speed & performance)
% =====================================================
:- table violation/2.
:- table red_light_violation/1.
:- table speeding_violation/1.
:- table wrong_lane_violation/1.
:- table no_helmet_violation/1.
:- table wrong_direction_violation/1.
:- table illegal_u_turn/1.

% --- NEW TABLED PREDICATES ---
:- table seatbelt_violation/1.
:- table phone_usage_violation/1.
:- table overloading_violation/1.
:- table no_parking_violation/1.
:- table speed_breaker_violation/1.

% =====================================================
% 3. HELPER PREDICATES
% =====================================================
valid_vehicle(Id) :-
    vehicle(Id, Type),
    member(Type, [car, bike, truck, bus]).

current_time(T) :-
    frame_time(T).

% =====================================================
% 4. VIOLATION RULES (Pure First-Order Logic)
% =====================================================

% Rule 1: Red Light Violation
red_light_violation(V) :-
    valid_vehicle(V),
    traffic_light(red, _),
    crossed_stop_line(V, _),
    \+ emergency_vehicle(V).

% Rule 2: Speeding (city limit 60 km/h - configurable)
speeding_violation(V) :-
    valid_vehicle(V),
    speed(V, S),
    S > 60,
    \+ emergency_vehicle(V).

% Rule 3: Wrong Lane / Solid Line Crossing
wrong_lane_violation(V) :-
    valid_vehicle(V),
    in_wrong_lane(V, solid).

% Rule 4: No Helmet (two-wheelers only)
no_helmet_violation(V) :-
    vehicle(V, bike),
    helmet(V, no).

% Rule 5: Wrong Direction (one-way)
wrong_direction_violation(V) :-
    valid_vehicle(V),
    direction(V, wrong_way).

% Rule 6: Illegal U-Turn (at no-u-turn zone)
illegal_u_turn(V) :-
    valid_vehicle(V),
    direction(V, u_turn),
    traffic_light(red, _).   % U-turn only illegal on red in our rule set

% -------------------------------------------------------
% NEW Rule 7: Seatbelt Violation (cars only)
% -------------------------------------------------------
seatbelt_violation(V) :-
    vehicle(V, car),
    seatbelt(V, no).

% -------------------------------------------------------
% NEW Rule 8: Mobile Phone Usage While Driving
% -------------------------------------------------------
phone_usage_violation(V) :-
    valid_vehicle(V),
    phone_usage(V, yes).

% -------------------------------------------------------
% NEW Rule 9: Overloading (bikes with more than 2 people)
% -------------------------------------------------------
overloading_violation(V) :-
    vehicle(V, bike),
    passenger_count(V, N),
    N > 2.

% -------------------------------------------------------
% NEW Rule 10: No Parking Zone Violation
% -------------------------------------------------------
no_parking_violation(V) :-
    valid_vehicle(V),
    parked(V, yes),
    zone_type(V, no_parking).

% -------------------------------------------------------
% NEW Rule 11: Over Speed at Speed Breaker
%              (limit = 20 km/h near a speed breaker)
% -------------------------------------------------------
speed_breaker_violation(V) :-
    valid_vehicle(V),
    near_speed_breaker(V, yes),
    speed(V, S),
    S > 20.

% =====================================================
% 5. UNIFIED VIOLATION PREDICATE
% =====================================================
violation(V, red_light)         :- red_light_violation(V).
violation(V, speeding)          :- speeding_violation(V).
violation(V, wrong_lane)        :- wrong_lane_violation(V).
violation(V, no_helmet)         :- no_helmet_violation(V).
violation(V, wrong_direction)   :- wrong_direction_violation(V).
violation(V, illegal_u_turn)    :- illegal_u_turn(V).
violation(V, no_seatbelt)       :- seatbelt_violation(V).
violation(V, phone_usage)       :- phone_usage_violation(V).
violation(V, overloading)       :- overloading_violation(V).
violation(V, no_parking)        :- no_parking_violation(V).
violation(V, speed_breaker)     :- speed_breaker_violation(V).

% =====================================================
% 6. EXPLANATION ENGINE (Recursive Proof Tree → English)
% =====================================================

explain_violation(V, Type, NaturalExplanation) :-
    violation(V, Type),
    findall(Reason, reason_for(Type, V, Reason), Reasons),
    atomic_list_concat(Reasons, ' AND ', ReasonString),
    format(atom(NaturalExplanation),
           'Vehicle ~w committed ~w violation because: ~w.',
           [V, Type, ReasonString]).

% -------------------------------------------------------
% Reasons for ORIGINAL violation types
% -------------------------------------------------------
reason_for(red_light, _, "traffic light was RED") :-
    traffic_light(red, _).
reason_for(red_light, V, "vehicle crossed the stop line") :-
    crossed_stop_line(V, _).
reason_for(red_light, V, "vehicle is NOT an emergency vehicle") :-
    \+ emergency_vehicle(V).

reason_for(speeding, V, Reason) :-
    speed(V, S),
    format(atom(Reason), "speed was ~w km/h (limit = 60 km/h)", [S]).

reason_for(wrong_lane, V, "vehicle crossed solid white/yellow line") :-
    in_wrong_lane(V, solid).

reason_for(no_helmet, _, "rider on two-wheeler is not wearing helmet").

reason_for(wrong_direction, _, "vehicle is moving in wrong direction (one-way road)").

reason_for(illegal_u_turn, _, "illegal U-turn attempted at red light").

% -------------------------------------------------------
% Reasons for NEW violation types
% -------------------------------------------------------

% Seatbelt
reason_for(no_seatbelt, V, "driver/passenger in car is not wearing seatbelt") :-
    vehicle(V, car),
    seatbelt(V, no).

% Phone Usage
reason_for(phone_usage, V, "driver was detected using mobile phone while driving") :-
    phone_usage(V, yes).

% Overloading
reason_for(overloading, V, Reason) :-
    passenger_count(V, N),
    format(atom(Reason),
           "bike has ~w passengers (maximum allowed = 2)", [N]).

% No Parking
reason_for(no_parking, V, "vehicle is parked in a no-parking zone") :-
    parked(V, yes),
    zone_type(V, no_parking).

% Speed Breaker
reason_for(speed_breaker, V, Reason) :-
    speed(V, S),
    format(atom(Reason),
           "speed was ~w km/h near speed breaker (limit = 20 km/h)", [S]).

% =====================================================
% 7. PUBLIC API (called from Python)
% =====================================================

% Assert facts coming from CV (list of terms)
assert_facts(FactList) :-
    forall(member(Fact, FactList), assertz(Fact)).

% Clear everything before new frame
retract_all_facts :-
    retractall(vehicle(_, _)),
    retractall(traffic_light(_, _)),
    retractall(crossed_stop_line(_, _)),
    retractall(speed(_, _)),
    retractall(in_wrong_lane(_, _)),
    retractall(helmet(_, _)),
    retractall(emergency_vehicle(_)),
    retractall(direction(_, _)),
    retractall(frame_time(_)),
    % --- NEW FACTS CLEANUP ---
    retractall(seatbelt(_, _)),
    retractall(phone_usage(_, _)),
    retractall(passenger_count(_, _)),
    retractall(parked(_, _)),
    retractall(zone_type(_, _)),
    retractall(near_speed_breaker(_, _)).

clear_knowledge_base :-
    retract_all_facts.

% Get all violations in current frame
list_all_violations(Violations) :-
    findall(V-Type, violation(V, Type), Violations).

% =====================================================
% 8. UTILITIES & DEBUG
% =====================================================
show_knowledge_base :-
    listing(vehicle),
    listing(traffic_light),
    listing(crossed_stop_line),
    listing(speed),
    listing(seatbelt),
    listing(phone_usage),
    listing(passenger_count),
    listing(parked),
    listing(zone_type),
    listing(near_speed_breaker).

% =====================================================
% 9. SAMPLE TEST — load with: ?- run_tests.
% =====================================================
run_tests :-
    write('=== Loading test facts ==='), nl,
    assert_facts([
        frame_time(t_001),

        % Vehicles
        vehicle(car_001, car),
        vehicle(bike_002, bike),
        vehicle(truck_003, truck),
        vehicle(car_004, car),
        vehicle(bike_005, bike),

        % Traffic light
        traffic_light(red, t_001),

        % Speeds
        speed(car_001, 85),        % speeding
        speed(bike_002, 40),
        speed(truck_003, 55),
        speed(car_004, 30),
        speed(bike_005, 25),       % over speed breaker limit

        % Stop line crossings
        crossed_stop_line(car_001, t_001),

        % Lane
        in_wrong_lane(bike_002, solid),

        % Helmet
        helmet(bike_002, no),

        % Direction
        direction(truck_003, wrong_way),

        % --- NEW FACTS ---
        seatbelt(car_001, no),           % no seatbelt
        phone_usage(car_004, yes),       % using phone
        passenger_count(bike_005, 3),    % overloaded
        parked(truck_003, yes),
        zone_type(truck_003, no_parking),% parked illegally
        near_speed_breaker(bike_005, yes)% speeding at breaker
    ]),
    write('=== All Violations Detected ==='), nl,
    list_all_violations(Vs),
    forall(member(V-T, Vs), (
        explain_violation(V, T, Exp),
        writeln(Exp)
    )),
    write('=== Clearing Facts ==='), nl,
    retract_all_facts.

% =====================================================
% 10. INITIALIZATION
% =====================================================
:- initialization(write('Traffic Violation Prolog Engine Loaded Successfully!\n')).