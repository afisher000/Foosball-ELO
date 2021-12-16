% PBPL Foosball ELO Rating System
% Written by Andrew Fisher
% August 2019

% THIS FUNCTION READS IN EXCEL TABLES, CHECKS FOR ERRORS IN THE DATA ENTRY,
% AND ADDS A COLUMN OF ORDINAL DATES TO GL.

function [GL,R,numplayers,error]=ReadCheckLog()

%% Read in Initial Rankings (R) and Game Log (GL)
GL=readtable('Game Log.xlsx');
R=readtable('Initial Ratings.xlsx');
numplayers=width(R);


%% Error Check for Game Log
error=0;
for i=1:height(GL)
    % Check that names are spelled correctly
    for j=1:4
        if not(ismember(GL{i,j},R.Properties.VariableNames))
                fprintf(strcat(GL{i,j}{1},' at location (%i,%i) in game log \n'),[i+1,j]); % i+1 to match excel row
                error=1;
        end
    end
    % Check that score is an integer from 1 to 9
    if not(ismember(GL{i,5},0:1:9))
        fprintf(strcat(num2str(GL{i,5}),' at location (%i,5) in game log \n'),i+1); % i+1 to match excel row
        error=1;
    end
end
if error==1
    fprintf('Fix errors in game log...\n\n');
    return 
elseif error==0
    fprintf('No errors in game log...\n\n');
end

%% Add Ordinal Dates
Date=GL{:,{'Date'}};
OrdDate=zeros(height(GL),1);
for i=1:height(GL)
    OrdDate(i)=datenum(Date(i));
end
GL=[GL table(OrdDate)];
