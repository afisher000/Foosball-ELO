% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

function Main()
close all;
clear vars;
format long;

%% Read In Logs
[GL,R,numplayers,error]=ReadCheckLog();
if error==1
    return;
end

R_single=R;
R_double=R;
%% Split GL into doubles and singles
scn=strcmp(GL{:,1},GL{:,2});
GL_single=GL(scn,:);
GL_double=GL(~scn,:);

%% Update Ratings
[R_double]=Simulate(GL_double,R_double);
[R_single]=Simulate(GL_single,R_single);

%% Compute Rankings
inputdate='4/12/2020';
Rankings(GL_double,R_double,'MainResults_doubles.xlsx',numplayers,inputdate);
Rankings(GL_single,R_single,'MainResults_singles.xlsx',numplayers,inputdate);

%% Plot Ratings
PlotRatings(R_double,numplayers);
PlotRatings(R_single,numplayers);

%% Save Backup of Foosball Log
fileID=strcat('Foosball Backup\\FoosballLogBackup_',datestr(datetime('today')),'.xlsx');
writetable(GL,fileID);