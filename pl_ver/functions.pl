%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% System Built-in Functions %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% member function.
member(X, [X|_]).
member(X, [A|T]) :- A \= X, member(X, T).

neg_member(X, []).
neg_member(X, [Y|T]) :- X \= Y, neg_member(X, T).
% neg_member(X, Y) :- member(X, Y), !, fail.
% neg_member(X, Y).

% append function.
append([], L, L).
append([H|T], L, [H|R]) :- append(T, L, R).

% select function.
select(A, [A|T], T).
select(A, [H|T], [H|R]) :- A \= H, select(A, T, R).

% merge function.
merge([], A, A).
merge([H|T], B, C) :- member(H, B), merge(T, B, C).
merge([H|T], B, D) :- neg_member(H, B), append(B, [H], C), merge(T, C, D).

% intersection function.
intersection([], _, []).
intersection([H|T], L, [H|Res]) :- member(H, L), intersection(T, L, Res).
intersection([H|T], L, Res) :- not member(H, L), intersection(T, L, Res).

% replace function. (replace(A, B, L1, L2) :- replace item A from L1 to B to get L2.)
replace(_, _, [], []).
replace(O, R, [O|T1], [R|T2]) :- replace(O, R, T1, T2).
replace(O, R, [H|T1], [H|T2]) :- H \= O, replace(O, R, T1, T2).

% subtract function. subtract(A, B, C) :- A-B=C.
subtract([], _, []).
subtract([A|C], B, D) :- member(A, B), subtract(C, B, D).
subtract([A|B], C, [A|D]) :- neg_member(A, C), subtract(B, C, D).

% length function.
length([], N, N).
length([_|L], N, N0) :- N1 is N0 + 1, length(L, N, N1).
length(L, N) :- length(L, N, 0).

% unique function. make the list element unique.
unique([], []).
unique([X|Xs], [X|Ys]) :- subtract(Xs, [X], Zs), unique(Zs, Ys).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Predefined Knowledge %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

topic('movie'). topic('person'). topic('book').
% potential topic: film studio, soundtrack, country/culture, film series.

% General Topic-Attribute Mapping.
has_attr('movie', X, Attr, Value) :- movie(X, Attr, Value).
has_attr('person', X, Attr, Value) :- person(X, Attr, Value).
has_attr('book', X, Attr, Value) :- book(X, Attr, Value).

% Random functions.
continue_topic :- continue_attr.
continue_topic :- random(1, 10, X), X < 7.
continue_attr :- random(1, 10, X), X < 3.

% Recommend parameters
recommend_num(3).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% CKT Processing %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Response attr has different list.
response_attr('movie', Attr) :- member(Attr, ['plot episode', 'line', 'scene', 'costume', 'language', 'award', 'music', 'value expressed', 'characterization', 'technique', 'cinematography', 'editing', 'actor performance', 'adaptation', 'director', 'social impact']).
response_attr('person', Attr) :- member(Attr, ['filmography', 'skill', 'award', 'appearance', 'personal life']).
response_attr('book', Attr) :- member(Attr, ['storyline', 'writing style', 'symbolism', 'emotion impact', 'social background']).

% Outer Conversation Loop - Controling the conversation topics.
next_topic(Topic, Name, Attr, 'None', 'None') :- round(I), hist(I, Topic, Name, Attr, Attitude, 'user'), not discussed_before(Topic, Name, Attr).
next_topic(Topic, Name, Attr, 'None', 'None') :- continue_topic, talk(Topic, Name, Attr1), next_attr(Topic, Name, Attr).
next_topic(Topic, Name, Attr, Source, Relation) :- len_rcc(I), random(1, I, N), rcc(N, Topic, Name, Source, Relation), next_attr(Topic, Name, Attr).

discussed_before(Topic, Name, Attr) :- round(I), !, hist(I, Topic, Name, Attr, Attitude, 'user'), hist(J, Topic, Name, Attr, Attitude, From), I \= J.

% Conversation Knowledge Template - Controling the conversation in a topic.
next_attr(Topic, Name, Attr) :- continue_attr, talk(Topic, Name, Attr), response_attr(Topic, Attr).
next_attr(Topic, Name, Attr) :- response_attr(Topic, Attr), not neg_next_attr(Topic, Name, Attr).
neg_next_attr(Topic, Name, Attr) :- not next_attr(Topic, Name, Attr).
neg_next_attr(Topic, Name, Attr) :- hist(I, Topic, Name, Attr, Attitude, From).

% Answer the question if user asks.
talk(Topic, Name, Attr, Value) :- talk(Topic, Name, Attr), attitude('ask'), data_attr(Topic, Name, Attr, Value), !.
talk(Topic, Name, Attr, 'None') :- talk(Topic, Name, Attr), attitude('ask'), not data_attr(Topic, Name, Attr, Value).
get_answer_list(L) :- findall(talk(Topic, Name, Attr, Answer), talk(Topic, Name, Attr, Answer), L).

% To see if the new attitude is agree with the old.
if_agree(Attitude, 'None') :- attitude('ask').
if_agree('ask', 'None').
if_agree(Attitude, 'agree') :- attitude(Attitude), Attitude \= 'ask'.
if_agree(Attitude1, 'disagree') :- attitude(Attitude2), Attitude1 \= Attitude2, Attitude1 \= 'ask', Attitude2 \= 'ask'.

% To check if switch attitude.
get_attitude(talk(Topic, Name, Attr), Attitude) :- hist(I, Topic, Name, Attr, Attitude, 'user').
get_attitude(Next, Attitude) :- random(1, 2, X), random_attitude(X, Attitude).

opposite_attitude('positive', 'negative').
opposite_attitude('negative', 'positive').

random_attitude(2, 'positive').
random_attitude(1, 'negative').

% Total step for next topic generation.
next_topic_total(talk(Topic, Name, Attr), attitude(Attitude), if_agree(If_Agree), Source, Relation) :-
    next_topic(Topic, Name, Attr, Source, Relation), get_attitude(talk(Topic, Name, Attr), Attitude), if_agree(Attitude, If_Agree).

% Recommend if find enough matched attributes.
recommend(recommend(Topic, Name), Reasons) :- matched_attr(Topic, Name, Reasons, N), recommend_num(M), N >= M, not hist_recommend(Topic, Name).

hist_recommend(Topic, Name) :- hist(I, Topic, Name, Attr, Attitude, From).

% Choose which mode to apply next.
next_action('quit', Answer, Next, Attitude, If_Agree, Source, Relation) :- quit, !.
next_action('irrelevant', Answer, Next, Attitude, If_Agree, Source, Relation) :- irrelevant, !, next_topic_total(Next, Attitude, If_Agree, Source, Relation).
next_action(Mode, Answer, Next, Attitude, If_Agree, Source, Relation) :- get_answer_list(Answer), !, next_action(Mode, Next, Attitude, If_Agree, Source, Relation).

next_action('recommend', Next, Attitude, If_Agree, Source, Relation) :- recommend(Next, Source), !.
next_action('general', Next, Attitude, If_Agree, Source, Relation) :- next_topic_total(Next, Attitude, If_Agree, Source, Relation).

% test
% ?- random(X), random(Y), random(Z).

