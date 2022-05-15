% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

% THIS FUNCTION RETURNS THE SUM OF THE SQUARES BETWEEN THE INITIAL RATINGS
% AND FINAL RATINGS

function output=ErrorFcn(x,GL,R)
numplayers=width(R);
R(1,1:numplayers)=num2cell(x);  % Replace ratings in R
R=Simulate(GL,R);
y=R{end,1:numplayers};
output=(x-y)*(x-y)'             % Display Output
