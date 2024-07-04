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


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Knowledge Processing %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A entity has three types of attributes: facts (only answer when asked), points (can be discussed), and links (jump to another entity)
movie(X) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'title', Title) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'is adult', Adult) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'year', Year) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'runtime', Runtime) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'genre', Genre) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'rating', Rating) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).
movie(X, 'number of votes', NumVotes) :- movie(X, Title, Adult, Year, Runtime, Genre, Rating, NumVotes).

person(X) :- person(X, Name, Birth, Death, Profession, Works).
person(X, 'name', Name) :- person(X, Name, Birth, Death, Profession, Works).
person(X, 'birth', Birth) :- person(X, Name, Birth, Death, Profession, Works).
person(X, 'death', Death) :- person(X, Name, Birth, Death, Profession, Works).
person(X, 'profession', Profession) :- person(X, Name, Birth, Death, Profession, Works).
person(X, 'works', Works) :- person(X, Name, Birth, Death, Profession, Works).

award(X) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'title', Title) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'start year', StartYear) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'categories', Categories) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'hold city', HoldCity) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'eligibility', Eligibility) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'statuette', Statuette) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).
award(X, 'criticisms', Criticisms) :- award(X, Title, StartYear, Categories, HoldCity, Eligibility, Statuette, Criticisms).

attend_in(Person, Movie) :- attend_in(Movie, _, Person, Job, JobType, Character).
attend_in(Person, Movie, 'job', Job) :- attend_in(Movie, _, Person, Job, JobType, Character).

win_award_movie(Movie, Award) :- win_award_movie(Award, Year, Category, Movie, Winner).
win_award_movie(Movie, Award, 'year', Year) :- win_award_movie(Award, Year, Category, Movie, Winner).
win_award_movie(Movie, Award, 'category', Category) :- win_award_movie(Award, Year, Category, Movie, Winner).
win_award_movie(Movie, Award, 'winner', Winner) :- win_award_movie(Award, Year, Category, Movie, Winner).

win_award_person(Person, Award) :- win_award_person(Award, Year, Category, Person, Winner).
win_award_person(Person, Award, 'year', Year) :- win_award_person(Award, Year, Category, Person, Winner).
win_award_person(Person, Award, 'category', Category) :- win_award_person(Award, Year, Category, Person, Winner).
win_award_person(Person, Award, 'winner', Winner) :- win_award_person(Award, Year, Category, Person, Winner).

topic('movie'). topic('person').
% potential topic: film studio, soundtrack, country/culture, film series.

% General Topic-Attribute Mapping.
has_attr('movie', X, Attr, Value) :- movie(X, Attr, Value).
has_attr('person', X, Attr, Value) :- person(X, Attr, Value).
has_attr('award', X, Attr, Value) :- award(X, Attr, Value).

% The relation of the topics.
related('movie', Movie, 'person', Person, 'None') :- attend_in(Person, Movie).
related('person', Person, 'movie', Movie, 'None') :- attend_in(Person, Movie).
related('movie', Movie, 'award', Award, 'None') :- win_award_movie(Movie, Award).
related('award', Award, 'movie', Movie, 'None') :- win_award_movie(Movie, Award).
related('person', Person, 'award', Award, 'None') :- win_award_person(Person, Award).
related('award', Award, 'person', Person, 'None') :- win_award_person(Person, Award).

related('movie', Movie1, 'movie', Movie2, [reason('person', Person)]) :- attend_in(Person, Movie1), attend_in(Person, Movie2), Movie1 \= Movie2.

related('movie', Movie1, 'movie', Movie2, [reason('award', Award), reason('year', Year), reason('winner', 'True')]) :- win_award_movie(Movie1, Award, 'winner', 'True'), win_award_movie(Movie2, Award, 'winner', 'True'),
    win_award_movie(Movie1, Award, 'year', Year), win_award_movie(Movie2, Award, 'year', Year), Movie1 \= Movie2.
related('movie', Movie1, 'movie', Movie2, [reason('award', Award), reason('category', Category), reason('year', Year)]) :- win_award_movie(Movie1, Award, 'category', Category), win_award_movie(Movie2, Award, 'category', Category),
    win_award_movie(Movie1, Award, 'year', Year), win_award_movie(Movie2, Award, 'year', Year), Movie1 \= Movie2.
related('movie', Movie1, 'movie', Movie2, [reason('award', Award), reason('category', Category), reason('winner', 'True')]) :- win_award_movie(Movie1, Award, 'winner', 'True'), win_award_movie(Movie2, Award, 'winner', 'True'), 
    win_award_movie(Movie1, Award, 'category', Category), win_award_movie(Movie2, Award, 'category', Category), Movie1 \= Movie2.

related('person', Person1, 'person', Person2, [reason('movie', Movie)]) :- attend_in(Person1, Movie), attend_in(Person2, Movie), Person1 \= Person2.

related('person', Person1, 'person', Person2, [reason('award', Award), reason('year', Year), reason('winner', 'True')]) :- win_award_person(Person1, Award, 'winner', 'True'), win_award_person(Person2, Award, 'winner', 'True'),
    win_award_person(Person1, Award, 'year', Year), win_award_person(Person2, Award, 'year', Year), Person1 \= Person2.
related('person', Person1, 'person', Person2, [reason('award', Award), reason('category', Category), reason('year', Year)]) :- win_award_person(Person1, Award, 'category', Category), win_award_person(Person2, Award, 'category', Category),
    win_award_person(Person1, Award, 'year', Year), win_award_person(Person2, Award, 'year', Year), Person1 \= Person2.
related('person', Person1, 'person', Person2, [reason('award', Award), reason('category', Category), reason('winner', 'True')]) :- win_award_person(Person1, Award, 'winner', 'True'), win_award_person(Person2, Award, 'winner', 'True'), 
    win_award_person(Person1, Award, 'category', Category), win_award_person(Person2, Award, 'category', Category), Person1 \= Person2.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% CKT Processing %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Look up the name.
get_name(Topic, TID, Name) :- member(Topic, ['movie', 'award']), has_attr(Topic, TID, 'title', Name).
get_name(Topic, TID, Name) :- member(Topic, ['person']), has_attr(Topic, TID, 'name', Name).
get_name('None', 'None', 'None').

% Response attr has different list.
response_attr('movie', Attr) :- member(Attr, ['plot episode', 'line', 'scene', 'costume', 'language', 'genre', 'award', 'music', 'value expressed', 'characterization', 'technique', 'cinematography', 'editing', 'actor performance', 'adaptation', 'director', 'social impact']).
response_attr('person', Attr) :- member(Attr, ['filmography', 'skill', 'award', 'appearance', 'personal life']).

% Processing the state.
attr(Topic, Attr, TID, Attitude) :- talk(Topic, Name, Attr, Attitude), get_name(Topic, TID, Name).
attr(Topic, Attr, TID, Attitude) :- talk(Topic, Name, Attitude), get_name(Topic, TID, Name).

% Maintain a Relevant Consistent Concept (RCC) list.
find_rcc(attr(Topic, Attr, TID, Attitude), List) :- findall(related(Topic, TID, Topic1, T1ID, Reason), related(Topic, TID, Topic1, T1ID, Reason), List).

find_rcc_list(Attrs, List) :- find_rcc_list(Attrs, [], List).
find_rcc_list([], List, List).
find_rcc_list([X|Attrs], Temp, List) :- find_rcc(X, L), append(Temp, L, Next), find_rcc_list(Attrs, Next, List).

add_list_rcc([], RCC_List, RCC_List).
add_list_rcc([X|New], RCC_List, [X|Rest]) :- neg_member(X, RCC_List), add_list_rcc(New, RCC_List, Rest).
add_list_rcc([X|New], RCC_List, [X|Rest]) :- select(X, RCC_List, R), add_list_rcc(New, R, Rest).

clean_rcc([], [], _).
clean_rcc([X|RCC_List], Rest, AttrList) :- attr_member_rcc(X, AttrList), clean_rcc(RCC_List, Rest, AttrList).
clean_rcc([X|RCC_List], [X|Rest], AttrList) :- neg_attr_member_rcc(X, AttrList), clean_rcc(RCC_List, Rest, AttrList).

update_rcc(New, RCC, Ref, Updated) :- find_rcc_list(New, User_rcc_list), clean_rcc(User_rcc_list, Cleaned_RCC, Ref),
    add_list_rcc(Cleaned_RCC, RCC, New_RCC_List), unique(New_RCC_List, Updated).

% function: attr_member_rcc: tell if one topic-attr is in the rcc as target.
attr_member_rcc(related(Topic1, T1ID, Topic, TID, Reason), [attr(Topic, Attr, TID)|RCC_List]).
attr_member_rcc(related(Topic1, T1ID, Topic2, T2ID, Reason), [attr(Topic, Attr, TID)|RCC_List]) :- T2ID \= TID,
    attr_member_rcc(related(Topic1, T1ID, Topic2, T2ID, Reason), RCC_List).

neg_attr_member_rcc(related(Topic1, T1ID, Topic2, T2ID, Reason), []).
neg_attr_member_rcc(related(Topic1, T1ID, Topic2, T2ID, Reason), [attr(Topic, Attr, TID)|RCC_List]) :- T2ID \= TID, 
    neg_attr_member_rcc(related(Topic1, T1ID, Topic2, T2ID, Reason), RCC_List).

% Outer Conversation Loop - Controling the conversation topics.
next_topic(Topic, TID, 'None', 'None', 'None', RCC_List) :- continue_topic, attr(Topic, Attr, TID, Attitude), recent_rcc(RCC), recent_attr(AttrList),
    findall(attr(T, A, Tid, Att), attr(T, A, Tid, Att), Topics), update_rcc(Topics, RCC, AttrList, RCC_List).
next_topic(Topic, TID, Source_Topic, Source_TID, Reason, RCC_List) :- recent_rcc(RCC), recent_attr(AttrList),
    findall(attr(T, A, Tid, Att), attr(T, A, Tid, Att), Topics), update_rcc(Topics, RCC, AttrList, Updated_RCC_List), 
    select(related(Source_Topic, Source_TID, Topic, TID, Reason), Updated_RCC_List, Selected_RCC_List), 
    update_rcc(attr(Topic, Attr, TID, Attitude), Selected_RCC_List, [attr(Topic, Attr, TID, Attitude)], RCC_List).

% Conversation Knowledge Template - Controling the conversation in a topic.
next_attr(Topic, TID, Attr, Attitude, 'None') :- continue_attr, attr(Topic, Attr, TID, Attitude), response_attr(Topic, Attr).
next_attr(Topic, TID, Attr, 'None', 'None') :- response_attr(Topic, Attr), not neg_next_attr(Topic, TID, Attr, 'None', 'None').
neg_next_attr(Topic, TID, Attr, 'None', 'None') :- not next_attr(Topic, TID, Attr, 'None', 'None').
neg_next_attr(Topic, TID, Attr, Attitude, Value) :- recent_attr(AttrList), member(attr(Topic, Attr, TID), AttrList).

% Update the state.
update_attr(Next, AttrList) :- recent_attr(L), findall(attr(Topic, Attr, TID, Attitude), attr(Topic, Attr, TID), L1),
    append(L1, L, L2), append([Next], L2, L3), unique(L3, AttrList).

% Answer the question if user asks.
get_answer(Value) :- talk(Topic, Name, Attr, 'ask'), get_name(Topic, TID, Name), has_attr(Topic, TID, Attr, Value).
get_answer_list(L) :- findall(get_answer(Answer), get_answer(Answer), L).

% To see if the new attitude is agree with the old.
if_agree('ask', Attitude, 'None').
if_agree(Attitude, 'ask', 'None').
if_agree(Attitude, Attitude, 'agree') :- Attitude \= 'ask'.
if_agree(Attitude1, Attitude2, 'disagree') :- Attitude1 \= Attitude2, Attitude1 \= 'ask', Attitude2 \= 'ask'.

% Total step for next topic generation.
next_topic_total([If_Agree, New_Attitude, Topic_Name, Topic_Attr, Topic_Answer], [Source_Name, Reason], AttrList, RCC_List) :-
    attitude(New_Attitude), next_topic(Topic, TID, Source_Topic, Source_TID, Reason, RCC_List), next_attr(Topic, TID, Topic_Attr, Old_Attitude, Topic_Answer), 
    get_name(Topic, TID, Topic_Name), get_name(Source_Topic, Source_TID, Source_Name), update_attr(attr(Topic, Topic_Attr, TID), AttrList),
    if_agree(Old_Attitude, New_Attitude, If_Agree).

% Choose which mode to apply next.
next_action('quit', Answer, Next, Reason, AttrList, RCC_List) :- quit, !.
next_action('irrelevant', Answer, Next, Reason, AttrList, RCC_List) :- irrelevant, !, next_topic_total(Next, Reason, AttrList, RCC_List).
next_action('answer', Answer, Next, Reason, AttrList, RCC_List) :- get_answer(Answer), !, next_topic_total(Next, Reason, AttrList, RCC_List).
next_action('general', Answer, Next, Reason, AttrList, RCC_List) :- next_topic_total(Next, Reason, AttrList, RCC_List).

% test
%?- next_topic(Topic, TID, Source_Topic, Source_TID, Reason, RCC_List).

