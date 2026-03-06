%% =====================================================
%%  TRAFFIC VIOLATIONS EXPLAINABLE SYSTEM (Pure Prolog)
%%  File: traffic_violations.pl
%%  SWI-Prolog 8.4+ recommended
%%  Author: Your College Project (2026)
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
    frame_time/1.               % current frame timestamp

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

% Unified violation predicate
violation(V, red_light)       :- red_light_violation(V).
violation(V, speeding)        :- speeding_violation(V).
violation(V, wrong_lane)      :- wrong_lane_violation(V).
violation(V, no_helmet)       :- no_helmet_violation(V).
violation(V, wrong_direction) :- wrong_direction_violation(V).
violation(V, illegal_u_turn)  :- illegal_u_turn(V).

% =====================================================
% 5. EXPLANATION ENGINE (Recursive Proof Tree → English)
% =====================================================

explain_violation(V, Type, NaturalExplanation) :-
    violation(V, Type),
    findall(Reason, reason_for(Type, V, Reason), Reasons),
    atomic_list_concat(Reasons, ' AND ', ReasonString),
    format(atom(NaturalExplanation),
           'Vehicle ~w committed ~w violation because: ~w.',
           [V, Type, ReasonString]).

% Reasons for each violation type
reason_for(red_light, V, "traffic light was RED") :-
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

reason_for(no_helmet, V, "rider on two-wheeler is not wearing helmet").

reason_for(wrong_direction, V, "vehicle is moving in wrong direction (one-way road)").
reason_for(illegal_u_turn, V, "illegal U-turn attempted at red light").

% =====================================================
% 6. PUBLIC API (called from Python)
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
    retractall(frame_time(_)).

clear_knowledge_base :-
    retract_all_facts.

% Get all violations in current frame
list_all_violations(Violations) :-
    findall(V-Type, violation(V, Type), Violations).

% =====================================================
% 7. UTILITIES & DEBUG
% =====================================================
show_knowledge_base :-
    listing(vehicle),
    listing(traffic_light),
    listing(crossed_stop_line),
    listing(speed).

% =====================================================
% 8. INITIALIZATION (optional)
% =====================================================
:- initialization(write('Traffic Violation Prolog Engine Loaded Successfully!\n')).